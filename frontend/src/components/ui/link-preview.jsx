"use client";

import * as RdxHoverCard from "@radix-ui/react-hover-card";
import { encode } from "qss";
import React, { useState, useMemo, useCallback, useEffect } from "react";
import {
  AnimatePresence,
  motion,
  useMotionValue,
  useSpring,
} from "framer-motion";
import { cn } from "@/lib/utils";

function usePreviewSource(url, width, height, quality, isStatic, staticImageSrc) {
  return useMemo(() => {
    if (isStatic) {
      return staticImageSrc || "";
    }
    return url; // dynamic mode: caller should pass a backend proxy URL via imageSrc + isStatic
  }, [isStatic, staticImageSrc, url, width, height, quality]);
}

function useHoverState(followMouse) {
  const [isPeeking, setPeeking] = useState(false);
  const mouseX = useMotionValue(0);
  const springConfig = { stiffness: 120, damping: 20 };
  const followX = useSpring(mouseX, springConfig);

  const handlePointerMove = useCallback(
    (event) => {
      if (!followMouse) return;
      const target = event.currentTarget;
      const targetRect = target.getBoundingClientRect();
      const eventOffsetX = event.clientX - targetRect.left;
      const offsetFromCenter = (eventOffsetX - targetRect.width / 2) * 0.3;
      mouseX.set(offsetFromCenter);
    },
    [mouseX, followMouse]
  );

  const handleOpenChange = useCallback(
    (open) => {
      setPeeking(open);
      if (!open) {
        mouseX.set(0);
      }
    },
    [mouseX]
  );

  return { isPeeking, handleOpenChange, handlePointerMove, followX };
}

export const HoverPeek = ({
  children,
  url,
  className,
  peekWidth = 200,
  peekHeight = 125,
  imageQuality = 50,
  isStatic = false,
  imageSrc = "",
  enableMouseFollow = true,
  enableLensEffect = true,
  lensZoomFactor = 1.75,
  lensSize = 100,
}) => {
  const [imageLoadFailed, setImageLoadFailed] = useState(false);
  const finalImageSrc = usePreviewSource(
    url,
    peekWidth,
    peekHeight,
    imageQuality,
    isStatic,
    imageSrc
  );
  const { isPeeking, handleOpenChange, handlePointerMove, followX } =
    useHoverState(enableMouseFollow);

  const [isHoveringLens, setIsHoveringLens] = useState(false);
  const [lensMousePosition, setLensMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setImageLoadFailed(false);
  }, [finalImageSrc]);

  useEffect(() => {
    if (!isPeeking) {
      setImageLoadFailed(false);
      setIsHoveringLens(false);
    }
  }, [isPeeking]);

  const handleLensMouseMove = (e) => {
    if (!enableLensEffect) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setLensMousePosition({ x, y });
  };
  const handleLensMouseEnter = () => {
    if (enableLensEffect) setIsHoveringLens(true);
  };
  const handleLensMouseLeave = () => {
    if (enableLensEffect) setIsHoveringLens(false);
  };

  const cardMotionVariants = {
    initial: { opacity: 0, rotateY: -90, transition: { duration: 0.15 } },
    animate: {
      opacity: 1,
      rotateY: 0,
      transition: { type: "spring", stiffness: 200, damping: 18 },
    },
    exit: { opacity: 0, rotateY: 90, transition: { duration: 0.15 } },
  };

  const lensMotionVariants = {
    initial: { opacity: 0, scale: 0.7 },
    animate: {
      opacity: 1,
      scale: 1,
      transition: { duration: 0.2, ease: "easeOut" },
    },
    exit: {
      opacity: 0,
      scale: 0.7,
      transition: { duration: 0.2, ease: "easeIn" },
    },
  };

  const triggerChild = React.isValidElement(children)
    ? React.cloneElement(children, {
        className: cn(children.props.className, className),
        onPointerMove: handlePointerMove,
      })
    : (
      <span className={className} onPointerMove={handlePointerMove}>
        {children}
      </span>
    );

  return (
    <RdxHoverCard.Root
      openDelay={75}
      closeDelay={150}
      onOpenChange={handleOpenChange}
    >
      <RdxHoverCard.Trigger asChild>{triggerChild}</RdxHoverCard.Trigger>

      <RdxHoverCard.Portal>
        <RdxHoverCard.Content
          className="[perspective:800px] [--radix-hover-card-content-transform-origin:center_center] z-50"
          side="top"
          align="center"
          sideOffset={12}
          style={{ pointerEvents: enableLensEffect ? "none" : "auto" }}
        >
          <AnimatePresence>
            {isPeeking && (
              <motion.div
                variants={cardMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                style={{
                  x: enableMouseFollow ? followX : 0,
                  pointerEvents: "auto",
                }}
              >
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "relative block overflow-hidden rounded-lg bg-white dark:bg-neutral-900",
                    "border border-neutral-200 dark:border-neutral-700",
                    "shadow-lg hover:shadow-xl transition-shadow",
                    "p-0.5"
                  )}
                  onMouseEnter={handleLensMouseEnter}
                  onMouseLeave={handleLensMouseLeave}
                  onMouseMove={handleLensMouseMove}
                >
                  {imageLoadFailed ? (
                    <div
                      className="flex items-center justify-center bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400 text-xs font-sans"
                      style={{ width: peekWidth, height: peekHeight }}
                    >
                      Preview unavailable
                    </div>
                  ) : (
                    <img
                      src={finalImageSrc}
                      width={peekWidth}
                      height={peekHeight}
                      className="block rounded-[5px] pointer-events-none bg-neutral-50 dark:bg-neutral-800 align-top"
                      alt={`Link preview for ${url}`}
                      onError={() => setImageLoadFailed(true)}
                      loading="lazy"
                    />
                  )}

                  <AnimatePresence>
                    {enableLensEffect && isHoveringLens && !imageLoadFailed && (
                      <motion.div
                        className="absolute inset-0 pointer-events-none overflow-hidden rounded-lg"
                        variants={lensMotionVariants}
                        initial="initial"
                        animate="animate"
                        exit="exit"
                        style={{
                          maskImage: `radial-gradient(circle ${lensSize / 2}px at ${lensMousePosition.x}px ${lensMousePosition.y}px, black ${lensSize / 2}px, transparent ${lensSize / 2}px)`,
                          WebkitMaskImage: `radial-gradient(circle ${lensSize / 2}px at ${lensMousePosition.x}px ${lensMousePosition.y}px, black ${lensSize / 2}px, transparent ${lensSize / 2}px)`,
                        }}
                      >
                        <div
                          className="absolute inset-0"
                          style={{
                            transform: `scale(${lensZoomFactor})`,
                            transformOrigin: `${lensMousePosition.x}px ${lensMousePosition.y}px`,
                          }}
                        >
                          <img
                            src={finalImageSrc}
                            width={peekWidth}
                            height={peekHeight}
                            className="block rounded-[5px] bg-neutral-50 dark:bg-neutral-800 align-top"
                            alt=""
                            aria-hidden="true"
                          />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </a>
              </motion.div>
            )}
          </AnimatePresence>
        </RdxHoverCard.Content>
      </RdxHoverCard.Portal>
    </RdxHoverCard.Root>
  );
};
