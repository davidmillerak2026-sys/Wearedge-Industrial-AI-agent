# IQC Visual Check: AR Defect Highlighting

## Purpose

The in-process quality check verifies that the operator can identify surface scratches, missing fasteners, incorrect label orientation, and visible contamination before downstream assembly.

## Check Flow

1. Confirm the product variant and lot number.
2. Capture the AR camera frame at the station inspection point.
3. Compare defect bounding boxes against the active quality plan.
4. Ask the operator to confirm any ambiguous defect.
5. Place the unit on quality hold if a critical defect is confirmed.
6. Record the defect mode, image id, operator id, timestamp, and station id.

## Release Rule

A held unit can be released only when a quality engineer records disposition evidence. The agent can recommend release review, but it must not release the unit by itself.

