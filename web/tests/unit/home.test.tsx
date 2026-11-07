import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Home from "@/app/page";

describe("home page", () => {
  it("states the project promise and that nothing is published yet", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: "Sri Lanka Facts" })).toBeDefined();
    expect(screen.getByText(/Nothing here is published data yet/)).toBeDefined();
  });
});
