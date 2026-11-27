import { describe, expect, it } from "vitest";
import { cameraFor, percent, pointAlong, siteCenter, timeAgo, toMetres } from "./utils.js";

describe("map maths", () => {
  const center = { lat: 43.7734, lon: -79.5019 };

  it("the centre is at 0, 0", () => {
    const p = toMetres(center.lat, center.lon, center);
    expect(Math.abs(p.x)).toBeLessThan(0.001);
    expect(Math.abs(p.y)).toBeLessThan(0.001);
  });

  it("north is up (positive y)", () => {
    expect(toMetres(center.lat + 0.001, center.lon, center).y).toBeCloseTo(110.5, 0);
  });

  it("bearing 90 points east", () => {
    const p = pointAlong(0, 0, 90, 100);
    expect(p.x).toBeCloseTo(100);
    expect(p.y).toBeCloseTo(0);
  });

  it("site centre is the average of the sensors", () => {
    const c = siteCenter([{ lat: 1, lon: 2 }, { lat: 3, lon: 4 }]);
    expect(c).toEqual({ lat: 2, lon: 3 });
  });
});

describe("formatting", () => {
  it("time ago", () => {
    const now = Date.parse("2026-11-27T15:00:30Z");
    expect(timeAgo("2026-11-27T15:00:00Z", now)).toBe("30s ago");
    expect(timeAgo("2026-11-27T14:58:30Z", now)).toBe("2m ago");
  });

  it("percent", () => {
    expect(percent(0.934)).toBe("93%");
    expect(percent(null)).toBe("–");
  });

  it("finds the camera that saw an alert", () => {
    const sensors = [{ node_id: "rf-01", type: "remote_id" }, { node_id: "cv-02", type: "camera" }];
    expect(cameraFor({ sources: ["cv-02", "rf-01"] }, sensors).node_id).toBe("cv-02");
    expect(cameraFor({ sources: ["rf-01"] }, sensors)).toBeUndefined();
  });
});
