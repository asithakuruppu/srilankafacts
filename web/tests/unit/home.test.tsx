import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

import About from "@/app/about/page";

describe("about page", () => {
  it("states the promise and the national population from the release", () => {
    render(<About />);
    expect(
      screen.getByRole("heading", {
        name: /Every place in Sri Lanka, every number about it, with its source/i,
      }),
    ).toBeDefined();
    expect(screen.getByText("21,781,800")).toBeDefined();
    // The count depends on the release the test reads (fixture or local preview).
    expect(screen.getByRole("heading", { name: /^\d+ indicators in this preview$/ })).toBeDefined();
  });
});
