"use client"

import React from 'react';

interface ChatSkeletonProps {
  repeatCount?: number;
  pattern?: number[][];
  baseColorClass?: string;
  shimmerColorClass?: string;
  animationDuration?: number;
}

export default function LoadingChatPanel({
  repeatCount = 6,
  pattern = [
    [65, 35],          // Two-line greeting
    [90, 85, 55],      // Long paragraph
    [45, 20],          // Brief two-line acknowledgment
    [80, 60]           // Medium response
  ],
  baseColorClass = 'bg-app-loading', 
  shimmerColorClass = 'via-app-hover/80', 
  animationDuration = 1.5,
}: ChatSkeletonProps) {
  
  const skeletonMessages = Array.from({ length: repeatCount }).flatMap(() => pattern);

  return (
    // RESTORED: grow, h-full, and overflow-hidden
    <div 
      className="grow h-full flex flex-col w-full overflow-hidden"
      role="status"
      aria-label="Loading chat history"
    >
      <style>{`
        @keyframes shimmer-sweep {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer-sweep ${animationDuration}s infinite linear;
        }
      `}</style>

      {skeletonMessages.map((lineWidths, index) => (
        <div 
          key={index} 
          className="grid grid-cols-[auto_minmax(0,1fr)] gap-3 w-full px-3 py-3.5 mt-1"
        >
          {/* Avatar Skeleton */}
          <div className="mt-0.5">
            <div className={`relative overflow-hidden rounded-full w-10 h-10 ${baseColorClass}`}>
              <div className={`absolute inset-0 bg-gradient-to-r from-transparent ${shimmerColorClass} to-transparent animate-shimmer`} />
            </div>
          </div>

          {/* Message Lines Skeleton */}
          <div className="flex flex-col gap-2 mt-1">
            {lineWidths.map((width, lineIndex) => (
              <div 
                key={lineIndex} 
                className={`relative overflow-hidden h-4 rounded-md ${baseColorClass}`}
                style={{ width: `${width}%` }}
              >
                <div className={`absolute inset-0 bg-gradient-to-r from-transparent ${shimmerColorClass} to-transparent animate-shimmer`} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}