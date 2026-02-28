# Implementation Plan: Zomato EdgeVision

## Overview

This implementation plan focuses on building a hackathon demo of the Zomato EdgeVision system. The demo uses Next.js for the frontend (webcam capture + dashboard), FastAPI for the backend (verification ingestion + fraud detection + velocity calculation), and MongoDB for data persistence. AI verification uses Gemini/GPT-4o-mini Vision API as a proxy for on-device inference.

The implementation prioritizes the core demo flow: webcam capture → AI verification → fraud detection → velocity calculation → dashboard visualization. Testing tasks are marked as optional to enable faster MVP delivery.

## Tasks

- [x] 1. Project scaffolding and environment setup
  - Create Next.js 14 project with TypeScript and Tailwind CSS
  - Create FastAPI project with Python 3.11+ and async support
  - Set up MongoDB connection (local or Atlas)
  - Create `.env` files for API keys (Gemini/OpenAI, MongoDB URI, SECRET_SALT)
  - Install core dependencies (axios, recharts, shadcn/ui for frontend; motor, pydantic for backend)
  - Create basic project structure (frontend: pages, components, lib; backend: routers, services, models)
  - _Requirements: NFR 8 (Compatibility)_

- [ ] 2. Backend - Database schema and seed data
  - [x] 2.1 Create MongoDB collections and indexes
    - Define VerificationLog schema with indexes on (merchant_id, verified_timestamp) and order_id
    - Define MerchantVelocityState schema with unique index on merchant_id
    - Define Order schema with order_id, merchant_id, order_creation_timestamp, item_list
    - Define MenuItem schema with item_id, merchant_id, prep_time_minutes
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [x] 2.2 Create seed data script for demo
    - Generate 4 weeks of historical verification data for demo merchant (Friday 7PM-8PM, 20-30 orders/hour)
    - Generate sample orders with realistic prep times (3-15 minutes)
    - Generate menu items for demo merchant (10-15 items with varying prep times)
    - Script should be idempotent (can run multiple times without duplicates)
    - _Requirements: 9.1, 9.2 (Baseline Velocity Calculation)_

- [ ] 3. Backend - Cryptographic payload validation
  - [x] 3.1 Implement hash generation and validation functions
    - Write `generate_crypto_hash(order_id, timestamp, device_id, secret_salt)` using SHA-256
    - Write `validate_crypto_hash(order_id, timestamp, device_id, received_hash, secret_salt)` with constant-time comparison
    - Use XOR-based comparison to prevent timing attacks
    - _Requirements: 5.1, 5.2, 5.4, 14.1, 14.2, 14.3_

  - [ ] 3.2 Write property test for hash validation
    - **Property 1: Cryptographic Hash Integrity**
    - **Validates: Requirements 5, 14**
    - Test that generated hashes always validate successfully
    - Test that modified hashes always fail validation
    - Test constant-time comparison (timing variance < 1ms)

- [ ] 4. Backend - Ingestion endpoint
  - [x] 4.1 Create VerificationPayload Pydantic model
    - Define fields: order_id, verified_timestamp, confidence_score, crypto_hash, fallback_used, device_id
    - Add validation: order_id non-empty, timestamp positive, confidence_score in [0.0, 1.0], crypto_hash 64 chars
    - _Requirements: 5.2, 5.3_

  - [x] 4.2 Implement POST /api/v1/verify-order endpoint
    - Validate crypto_hash using validation function from task 3.1
    - Return HTTP 401 if hash invalid, log security event
    - Store VerificationPayload in MongoDB VerificationLog collection
    - Return success response with processing_time_ms
    - Handle MongoDB connection errors with HTTP 503
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 13.1, 13.2_

  - [ ] 4.3 Write unit tests for ingestion endpoint
    - Test successful verification with valid hash
    - Test rejection with invalid hash (HTTP 401)
    - Test MongoDB error handling (HTTP 503)
    - Test payload validation errors

- [ ] 5. Backend - Fraud detection (temporal validation)
  - [~] 5.1 Implement fraud detection service
    - Write `detect_fraud(order_id, verified_timestamp, db)` function
    - Calculate Delta = verified_timestamp - order_creation_timestamp
    - Query menu database for order items and get maximum prep_time_minutes
    - Flag as FRAUD_EMPTY_BAG if Delta < minimum_prep_time (minimum 60 seconds)
    - Flag as FRAUD_TEMPORAL_ANOMALY if Delta is negative
    - Return FraudFlag enum (FRAUD_EMPTY_BAG, FRAUD_TEMPORAL_ANOMALY, CLEAN)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6, 8.7_

  - [~] 5.2 Integrate fraud detection into ingestion endpoint
    - Call fraud detection service after hash validation
    - Store fraud_flag in VerificationLog document
    - Exclude fraud-flagged verifications from velocity calculation trigger
    - _Requirements: 8.5_

  - [ ] 5.3 Write property test for fraud detection
    - **Property 4: Fraud Detection Temporal Constraint**
    - **Validates: Requirement 8**
    - Test that Delta < min_prep_time always triggers FRAUD_EMPTY_BAG
    - Test that Delta >= min_prep_time always returns CLEAN
    - Test edge case where Delta exactly equals min_prep_time

- [~] 6. Checkpoint - Ensure backend ingestion and fraud detection work
  - Test ingestion endpoint with curl/Postman
  - Verify VerificationLog documents stored in MongoDB
  - Verify fraud detection flags premature scans correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Backend - Velocity calculation (Little's Law)
  - [~] 7.1 Implement baseline velocity calculation
    - Write `calculate_baseline_velocity(merchant_id, time_window_start, time_window_end, day_of_week, lookback_weeks, db)`
    - Query verification logs for last 4 weeks, same day of week and time window
    - Exclude fraud-flagged verifications
    - Calculate average orders per hour
    - Return 0.0 if insufficient data
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [~] 7.2 Implement current velocity calculation
    - Write `calculate_current_velocity(merchant_id, lookback_minutes, db)`
    - Query verification logs from last 15 minutes
    - Exclude fraud-flagged verifications
    - Extrapolate to hourly rate (orders per hour)
    - Return 0.0 if no verifications in window
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [~] 7.3 Implement invisible load ratio and KPT penalty calculation
    - Write `calculate_invisible_load_ratio(current_velocity, baseline_velocity)`
    - Return 1.0 if baseline_velocity is 0
    - Calculate ratio: current_velocity / baseline_velocity
    - Write `calculate_kpt_penalty(invisible_load_ratio)`
    - Return 0 if ratio >= 0.8
    - Return 15 minutes if ratio < 0.5
    - Use linear interpolation for ratio between 0.5 and 0.8
    - Clamp penalty to maximum 30 minutes
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 12.1, 12.2, 12.3, 12.4_

  - [~] 7.4 Implement velocity metrics calculation service
    - Write `calculate_velocity_metrics(merchant_id, db)` that orchestrates all calculations
    - Call baseline, current, ratio, and penalty functions
    - Store results in MerchantVelocityState collection (upsert)
    - Return VelocityMetrics dataclass with all fields
    - _Requirements: 11.6, 12.5, 13.6_

  - [ ] 7.5 Write property test for velocity calculation
    - **Property 5: Velocity Calculation Monotonicity**
    - **Validates: Requirements 10, 11, 12**
    - Test that lower velocity ratio produces higher or equal KPT penalty
    - Test that invisible_load_ratio is always non-negative
    - Test KPT penalty bounds (0 to 30 minutes)

- [ ] 8. Backend - Background worker for velocity updates
  - [~] 8.1 Create background task for velocity calculation
    - Implement async background task that runs every 5 minutes
    - Query distinct merchant_ids with verifications in last hour
    - Call `calculate_velocity_metrics` for each active merchant
    - Log results and errors
    - _Requirements: 10.5, 12.6_

  - [~] 8.2 Integrate background worker into FastAPI startup
    - Add startup event handler to launch background task
    - Ensure task runs continuously without blocking main event loop
    - _Requirements: 10.5_

- [ ] 9. Frontend - Webcam capture and frame processing
  - [~] 9.1 Create webcam capture component
    - Use browser MediaDevices API to access webcam
    - Display live video feed in UI
    - Capture frames at 3 FPS (throttle to reduce processing load)
    - Downscale frames to 640x640 resolution
    - Handle camera permission errors with user-friendly messages
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [~] 9.2 Create frame processing service
    - Convert video frame to base64-encoded image
    - Prepare payload for AI vision API (Gemini or GPT-4o-mini)
    - Send frame to AI API with prompt: "Detect food parcels and KOT receipts. Return bounding boxes for each detected object."
    - Parse API response to extract bounding boxes and class labels
    - _Requirements: 2.1, 2.2, 2.6_

  - [ ] 9.3 Write unit tests for frame processing
    - Test frame capture throttling (3 FPS)
    - Test frame downscaling to 640x640
    - Test base64 encoding
    - Mock AI API responses

- [ ] 10. Frontend - Spatial verification and debouncing logic
  - [~] 10.1 Implement bounding box intersection check
    - Write `checkBoundingBoxIntersection(foodBox, receiptBox)` function
    - Use separating axis theorem to detect intersection
    - Return true if boxes intersect or receipt is contained in food box
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

  - [~] 10.2 Implement three-frame debouncer
    - Write `processDetectionWithDebounce(detectionResult, state)` function
    - Maintain state with consecutiveFrames counter
    - Increment counter on successful spatial validation
    - Reset counter to 0 on validation failure
    - Return verification success when counter reaches 3
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 10.3 Write property test for spatial verification
    - **Property 2: Spatial Verification Constraint**
    - **Validates: Requirement 3**
    - Test that verification only succeeds when both classes detected and boxes intersect
    - Test various bounding box configurations (non-intersecting, partially intersecting, fully contained)

  - [ ] 10.4 Write property test for debouncing logic
    - **Property 3: Temporal Debouncing**
    - **Validates: Requirement 4**
    - Test that verification requires exactly 3 consecutive successful detections
    - Test state reset on failure
    - Test alternating success/failure patterns

- [ ] 11. Frontend - Cryptographic payload generation and submission
  - [~] 11.1 Implement payload generation
    - Write `generatePayload(orderId, timestamp, confidenceScore, fallbackUsed)` function
    - Generate SHA-256 hash: Hash(OrderID|Timestamp|DeviceID|SECRET_SALT)
    - Create JSON payload with order_id, verified_timestamp, confidence_score, crypto_hash, fallback_used
    - Do NOT include raw image data
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [~] 11.2 Implement payload submission to backend
    - Send POST request to /api/v1/verify-order with payload
    - Handle success response (200 OK)
    - Handle error responses (401 Unauthorized, 503 Service Unavailable)
    - Implement retry logic with exponential backoff (1s, 2s, 4s)
    - Store failed payloads in local storage for later retry
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 12. Frontend - Fallback mechanisms (flashlight and manual override)
  - [~] 12.1 Implement fallback timer
    - Track continuous inference failure duration
    - Trigger flashlight UI indicator at T+5 seconds
    - Display manual override button at T+10 seconds
    - Reset timer on successful verification
    - _Requirements: 6.1, 6.2, 6.6_

  - [~] 12.2 Implement manual override UI
    - Display input field for last 4 digits of Order ID
    - Validate input (4 digits, numeric only)
    - Show error message for invalid input
    - Generate payload with fallback_used=true
    - Submit payload to backend
    - _Requirements: 6.3, 6.4, 6.5_

  - [ ] 12.3 Write property test for fallback timing
    - **Property 6: Fallback Timer Guarantees**
    - **Validates: Requirement 6**
    - Test that flashlight triggers at 5 seconds
    - Test that manual override appears at 10 seconds
    - Test timing accuracy (±500ms tolerance)

- [ ] 13. Frontend - Split-screen dashboard UI
  - [~] 13.1 Create camera feed display
    - Show live webcam feed with bounding boxes overlaid
    - Draw green boxes for detected food parcels (Class 0)
    - Draw blue boxes for detected KOT receipts (Class 1)
    - Show verification status (waiting, verifying, success, failed)
    - Display consecutive frame counter (0/3, 1/3, 2/3, 3/3)
    - _Requirements: 1.1_

  - [~] 13.2 Create analytics dashboard
    - Display current velocity (orders/hour) with real-time updates
    - Display baseline velocity (orders/hour) from historical data
    - Display invisible load ratio (Ri) with color coding (green >= 0.8, yellow 0.5-0.8, red < 0.5)
    - Display active KPT penalty (minutes) with alert styling
    - Show line chart of velocity over time (last 1 hour)
    - Show verification log table (recent 10 verifications with timestamps and fraud flags)
    - _Requirements: 11.6, 12.5_

  - [~] 13.3 Add demo simulation controls
    - Add "Simulate Congestion" button to trigger velocity drop
    - Add "Reset Demo" button to clear data and reseed
    - Add "Inject Fraud" button to send premature verification
    - Display simulation status messages
    - _Requirements: Demo requirements_

- [~] 14. Checkpoint - Ensure frontend and backend integration works
  - Test complete flow: webcam capture → AI verification → payload submission → dashboard update
  - Verify bounding boxes display correctly on video feed
  - Verify dashboard updates in real-time when verifications occur
  - Test fallback mechanisms (flashlight, manual override)
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Demo simulation tools
  - [~] 15.1 Create time-lapse data spoofer endpoint
    - Add POST /api/v1/demo/seed-historical-data endpoint
    - Generate 4 weeks of fake verification data for demo merchant
    - Use realistic patterns (20-30 orders/hour on Friday 7PM-8PM)
    - Make endpoint idempotent
    - _Requirements: 9.1, 9.2_

  - [~] 15.2 Create congestion simulation endpoint
    - Add POST /api/v1/demo/simulate-congestion endpoint
    - Accept drop_percentage parameter (default 0.5)
    - Generate reduced verifications in last 15 minutes to simulate velocity drop
    - Trigger velocity recalculation
    - Return new velocity metrics
    - _Requirements: 11.3, 11.4, 12.2, 12.3_

  - [~] 15.3 Create fraud injection endpoint
    - Add POST /api/v1/demo/inject-fraud endpoint
    - Create verification with Delta < min_prep_time
    - Verify fraud detection flags it correctly
    - Return fraud detection result
    - _Requirements: 8.4, 8.5_

- [ ] 16. API documentation and demo script
  - [~] 16.1 Create API documentation
    - Document all backend endpoints with request/response examples
    - Include curl commands for testing
    - Document environment variables required
    - Add setup instructions for MongoDB
    - _Requirements: NFR 9 (Maintainability)_

  - [~] 16.2 Create demo script
    - Write step-by-step demo flow for 5-minute presentation
    - Include golden path scenario (successful verification)
    - Include fraud detection scenario (empty bag, loose receipt)
    - Include fallback scenario (dark environment, manual override)
    - Include velocity drop simulation
    - Add troubleshooting tips
    - _Requirements: Demo requirements_

- [ ] 17. Final integration and polish
  - [~] 17.1 Add error handling and user feedback
    - Display toast notifications for success/error states
    - Show loading spinners during API calls
    - Add error boundaries for React components
    - Log errors to console for debugging
    - _Requirements: 18.1, 18.2, 18.3, 18.4_

  - [~] 17.2 Performance optimization
    - Ensure frame processing completes within 200ms budget
    - Optimize AI API calls (use smaller image sizes if needed)
    - Add debouncing to dashboard updates
    - Minimize re-renders in React components
    - _Requirements: 19.1, 19.2, NFR 1_

  - [~] 17.3 UI polish and styling
    - Apply consistent Tailwind CSS styling
    - Add responsive design for different screen sizes
    - Improve accessibility (ARIA labels, keyboard navigation)
    - Add animations for state transitions
    - _Requirements: NFR 10 (Usability)_

- [~] 18. Final checkpoint - Demo readiness
  - Run through complete demo script end-to-end
  - Verify all 6 demo scenarios work flawlessly
  - Test on different browsers (Chrome, Firefox, Safari)
  - Verify MongoDB data persistence
  - Ensure all environment variables configured
  - Prepare backup plan for network failures
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Focus is on hackathon demo path (Next.js + FastAPI + Gemini API) rather than production path (React Native + TFLite)
- Demo simulation tools enable impressive live demonstrations without real merchant data
- The implementation prioritizes visual impact and core functionality over production-grade robustness
