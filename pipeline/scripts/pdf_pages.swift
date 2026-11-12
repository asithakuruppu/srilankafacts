// Extract text and render PNG images of chosen PDF pages (macOS only; uses PDFKit).
// Usage: swift scripts/pdf_pages.swift <pdf> <out_dir> <page> [<page> ...]
// Writes <out_dir>/page-NNN.txt and <out_dir>/page-NNN.png (1-based PDF page numbers).
// Used by the Q01 audit to compare release values with the DCS Final Report tables.
import AppKit
import PDFKit

let args = CommandLine.arguments
guard args.count >= 4, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
  FileHandle.standardError.write("usage: pdf_pages.swift <pdf> <out_dir> <page>...\n".data(using: .utf8)!)
  exit(2)
}
let out = URL(fileURLWithPath: args[2])
try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
for arg in args.dropFirst(3) {
  guard let n = Int(arg), n >= 1, n <= doc.pageCount, let page = doc.page(at: n - 1) else {
    FileHandle.standardError.write("bad page \(arg)\n".data(using: .utf8)!)
    exit(2)
  }
  let stem = String(format: "page-%03d", n)
  try (page.string ?? "").write(to: out.appendingPathComponent(stem + ".txt"), atomically: true, encoding: .utf8)
  let box = page.bounds(for: .mediaBox)
  let scale: CGFloat = 1.25
  let size = NSSize(width: box.width * scale, height: box.height * scale)
  let image = NSImage(size: size)
  image.lockFocus()
  NSColor.white.set()
  NSRect(origin: .zero, size: size).fill()
  let ctx = NSGraphicsContext.current!.cgContext
  ctx.scaleBy(x: scale, y: scale)
  page.draw(with: .mediaBox, to: ctx)
  image.unlockFocus()
  let rep = NSBitmapImageRep(data: image.tiffRepresentation!)!
  try rep.representation(using: .png, properties: [:])!.write(to: out.appendingPathComponent(stem + ".png"))
  print("wrote \(stem).txt and \(stem).png")
}
