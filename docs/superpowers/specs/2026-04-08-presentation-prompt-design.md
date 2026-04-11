# Presentation Prompt Design Spec

## Overview
Create a master prompt for Claude to generate a 5-minute PowerPoint presentation for the car price prediction platform demo. The prompt will produce a slide-by-slide script with titles, bullets, and speaker notes, emphasizing technical details over demo walkthrough.

## Requirements
- **Format**: Numbered slides with title, 3-5 bullets, and speaker notes.
- **Length**: 5-7 slides max, 5 minutes total.
- **Content Focus**: More technical (ML, backend, frontend choices), less on README scripts.
- **Browser Demo**: Include notes for live demo integration.

## Structure
- Slide 1: Introduction
- Slide 2: Demo Overview
- Slide 3-5: Technical Deep-Dive (with rationale for tech choices)
- Slide 6: Results & Impact
- Slide 7: Conclusion & Q&A

## Success Criteria
- Prompt generates copy-paste ready PowerPoint content.
- Engaging for academic presentation.
- Includes project context from README.

## Implementation Notes
- Prompt references existing README demo script but condenses it.
- Output is text-based for easy adaptation to PowerPoint.