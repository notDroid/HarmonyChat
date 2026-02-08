"use client"

import React, { useMemo } from 'react';

// --- 1. Configuration & Pattern Definition ---

const SKELETON_CONFIG = {
  // Appearance & Theme
  theme: {
    colorClass: 'bg-discord-loading', // Your global CSS variable class
    avatarSize: 'w-10 h-10',
    lineHeight: 'h-4',
    gap: 'gap-5',
    padding: 'px-4 py-4',
  },
  // Animation Physics
  animation: {
    duration: '2s',
    staggerPerMessage: 0.15, // Delay added per new message bubble
    staggerPerLine: 0.1,     // Delay added per line within a bubble
  },
  // The structure of the fake conversation
  pattern: {
    repeatCount: 6, // How many times to repeat the conversation block below
    conversationBlock: [
      { lines: [45] },              // Short greeting
      { lines: [92, 75, 60] },      // Long paragraph
      { lines: [25] },              // Short acknowledgment
      { lines: [70, 40] },          // Medium response
    ]
  }
};

// --- 2. Helper to Generate Data ---

/**
 * flattens the repeated blocks into a single linear array of messages
 * to prevent hydration mismatches and keep the list clean.
 */
const generateSkeletonData = () => {
  const { repeatCount, conversationBlock } = SKELETON_CONFIG.pattern;
  
  // Create an array of length `repeatCount` and fill it with the block
  return Array.from({ length: repeatCount }).flatMap(() => conversationBlock);
};

// --- 3. Sub-Components ---

const SkeletonLine = ({ width, delay }) => {
  const { theme, animation } = SKELETON_CONFIG;
  
  return (
    <div
      className={`${theme.lineHeight} ${theme.colorClass} rounded-md opacity-30 animate-pulse`}
      style={{
        width: `${width}%`,
        animationDelay: `${delay}s`,
        animationDuration: animation.duration,
      }}
    />
  );
};

const SkeletonMessage = ({ lineWidths, messageIndex }) => {
  const { theme, animation } = SKELETON_CONFIG;

  // Base delay for this specific message block
  const baseDelay = messageIndex * animation.staggerPerMessage;

  return (
    <div className="flex flex-row items-start w-full">
      {/* Avatar */}
      <div className="mr-4 shrink-0">
        <div 
          className={`${theme.avatarSize} rounded-full ${theme.colorClass} opacity-40 animate-pulse`} 
        />
      </div>

      {/* Message Lines */}
      <div className="flex flex-col flex-1 gap-2 mt-1">
        {lineWidths.map((width, lineIndex) => (
          <SkeletonLine 
            key={lineIndex} 
            width={width}
            // Add line index to base delay so lines wave downwards
            delay={baseDelay + (lineIndex * animation.staggerPerLine)}
          />
        ))}
      </div>
    </div>
  );
};

// --- 4. Main Component ---

export default function LoadingChatPanel() {
  const { theme } = SKELETON_CONFIG;
  
  // Memoize data generation so it doesn't recalculate on re-renders (if any occur)
  const skeletonMessages = useMemo(() => generateSkeletonData(), []);

  return (
    <div 
      className={`flex-grow h-full flex flex-col ${theme.padding} mb-1 overflow-hidden bg-transparent`}
      role="status"
      aria-label="Loading chat history"
    >
      <div className={`flex flex-col ${theme.gap}`}>
        {skeletonMessages.map((msg, index) => (
          <SkeletonMessage 
            key={index}
            messageIndex={index}
            lineWidths={msg.lines}
          />
        ))}
      </div>
    </div>
  );
}