// Text of every page of a PDF, two ways, for table extraction (macOS only; PDFKit + Vision).
// Usage: swift scripts/pdf_ocr.swift <out_dir> <pdf> [<pdf> ...]
// For each PDF, writes <out_dir>/<pdf file name>/page-NNN.txt (the PDF's own text layer, often
// empty for scans) and page-NNN.ocr.json (on-device Vision OCR of the rendered page: one object
// per recognised line with text, confidence and a bounding box in page fractions, origin top-left)
// and page-NNN.strip.json (a second OCR pass over the right half of the page only, where result
// sheets carry votes and percentages; boxes are mapped back to whole-page fractions) and
// page-NNN.col.json (a third pass over the votes column only, located from the "Votes Obtained"
// header found by the first pass; Vision reads isolated numbers far more reliably there).
// Nothing leaves the machine. Used by slf.datasets.election_results (Election Commission PDFs).
import AppKit
import PDFKit
import Vision

struct Line: Codable {
  let text: String
  let confidence: Float
  let x: Double
  let y: Double
  let w: Double
  let h: Double
}

func render(_ page: PDFPage, scale: CGFloat) -> CGImage? {
  let box = page.bounds(for: .mediaBox)
  let width = Int(box.width * scale)
  let height = Int(box.height * scale)
  guard let ctx = CGContext(
    data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
    space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)
  else { return nil }
  ctx.setFillColor(NSColor.white.cgColor)
  ctx.fill(CGRect(x: 0, y: 0, width: width, height: height))
  ctx.scaleBy(x: scale, y: scale)
  page.draw(with: .mediaBox, to: ctx)
  return ctx.makeImage()
}

func ocr(_ image: CGImage, x0: Double = 0, x1: Double = 1) throws -> [Line] {
  let request = VNRecognizeTextRequest()
  request.recognitionLevel = .accurate
  request.usesLanguageCorrection = false  // numbers and party codes, not prose
  request.recognitionLanguages = ["en-US"]
  try VNImageRequestHandler(cgImage: image, options: [:]).perform([request])
  return (request.results ?? []).compactMap { obs in
    guard let top = obs.topCandidates(1).first else { return nil }
    let b = obs.boundingBox  // normalised, origin bottom-left
    return Line(
      text: top.string, confidence: top.confidence, x: x0 + Double(b.minX) * (x1 - x0),
      y: Double(1 - b.maxY), w: Double(b.width) * (x1 - x0), h: Double(b.height))
  }
}

let args = CommandLine.arguments
guard args.count >= 3 else {
  FileHandle.standardError.write("usage: pdf_ocr.swift <out_dir> <pdf>...\n".data(using: .utf8)!)
  exit(2)
}
let outRoot = URL(fileURLWithPath: args[1])
let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
var failures = 0
for path in args.dropFirst(2) {
  let url = URL(fileURLWithPath: path)
  guard let doc = PDFDocument(url: url) else {
    FileHandle.standardError.write("cannot open \(path)\n".data(using: .utf8)!)
    failures += 1
    continue
  }
  let out = outRoot.appendingPathComponent(url.lastPathComponent)
  try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
  for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { continue }
    let stem = String(format: "page-%03d", i + 1)
    try (page.string ?? "").write(
      to: out.appendingPathComponent(stem + ".txt"), atomically: true, encoding: .utf8)
    guard let image = render(page, scale: 3.0) else {
      FileHandle.standardError.write("cannot render \(path) page \(i + 1)\n".data(using: .utf8)!)
      failures += 1
      continue
    }
    let lines = try ocr(image)
    try encoder.encode(lines).write(to: out.appendingPathComponent(stem + ".ocr.json"))
    let half = image.width / 2
    if let right = image.cropping(
      to: CGRect(x: half, y: 0, width: image.width - half, height: image.height))
    {
      let strip = try ocr(right, x0: Double(half) / Double(image.width))
      try encoder.encode(strip).write(to: out.appendingPathComponent(stem + ".strip.json"))
    }
    if let header = lines.first(where: { $0.text.lowercased().contains("votes obtained") }) {
      let c0 = max(0, header.x - 0.03)
      let c1 = min(1, header.x + header.w + 0.015)
      let px0 = Int(Double(image.width) * c0)
      let px1 = Int(Double(image.width) * c1)
      if let col = image.cropping(to: CGRect(x: px0, y: 0, width: px1 - px0, height: image.height)) {
        let read = try ocr(col, x0: Double(px0) / Double(image.width), x1: Double(px1) / Double(image.width))
        try encoder.encode(read).write(to: out.appendingPathComponent(stem + ".col.json"))
      }
    }
  }
  print("\(url.lastPathComponent): \(doc.pageCount) pages")
}
exit(failures == 0 ? 0 : 1)
