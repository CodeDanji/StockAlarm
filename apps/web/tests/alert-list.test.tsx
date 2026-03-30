import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { AlertList } from "../src/components/AlertList";

describe("AlertList", () => {
  it("renders alert names", () => {
    render(<AlertList alerts={[{ id: 1, name: "AAPL RSI", mode: "A", active: true }]} />);
    expect(screen.getByText("AAPL RSI")).toBeTruthy();
  });
});
