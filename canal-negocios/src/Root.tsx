import React from "react";
import { Composition, registerRoot } from "remotion";
import { Video } from "./Video";
import type { VideoProps } from "./schema";
import ejemplo from "../guiones/2026-11-04-crecer-sin-caja.json";
import { estimarTiming } from "./timing";

const FPS = 30;

const Root: React.FC = () => {
  const guion = ejemplo as VideoProps["guion"];
  return (
    <Composition
      id="Video"
      component={Video}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={FPS * 10}
      defaultProps={{ guion, timing: estimarTiming(guion), audio: null } satisfies VideoProps}
      calculateMetadata={({ props }) => ({
        durationInFrames: Math.ceil((props.timing.duracion + 0.6) * FPS),
      })}
    />
  );
};

registerRoot(Root);
