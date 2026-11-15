import { describe, expect, it } from "vitest";

import { colorExpression } from "@/components/map-view";

function stepArgs(expression: unknown): unknown[] | undefined {
  const caseExpr = expression as unknown[];
  const inner = caseExpr[2];
  return Array.isArray(inner) && inner[0] === "step" ? inner : undefined;
}

describe("colorExpression", () => {
  it("uses a flat colour when there are no class breaks", () => {
    const { expression } = colorExpression(false, [], null);
    expect(stepArgs(expression)).toBeUndefined();
  });

  it("emits a valid step (at least 4 args) with one break", () => {
    const step = stepArgs(colorExpression(false, [5], null).expression);
    expect(step && step.length).toBeGreaterThanOrEqual(4);
  });

  it("emits a valid step for compare mode with no breaks", () => {
    const step = stepArgs(colorExpression(true, [], 10).expression);
    expect(step && step.length).toBeGreaterThanOrEqual(4);
  });
});
