# Requirements Document: Zomato EdgeVision

## Introduction

Zomato EdgeVision is an edge-computing system that replaces manual "Food Ready" merchant signals with AI-verified timestamps using cryptographic proof. The system addresses three critical business problems: (1) eliminating unreliable manual merchant signals that cause delivery delays, (2) detecting invisible kitchen load from dine-in customers and competitor platform orders that slow down Zomato order preparation, and (3) dynamically adjusting Kitchen Prep Time (KPT) estimates based on real-time kitchen throughput velocity.

The system operates under strict technical constraints: zero cloud video streaming (all AI inference happens on-device), sub-200ms latency for merchant workflow, and zero new hardware requirements (uses existing merchant smartphones). The architecture separates edge processing (mobile device) from cloud analytics (backend microservices) to bypass network bottlenecks in Indian kitchen environments.

## Business Objectives

1. **Replace Manual Signals**: Eliminate unreliable manual "Food Ready" button presses with automated AI verification, reducing false signals by 80%
2. **Detect Invisible Load**: Identify kitchen congestion from non-Zomato orders (dine-in, competitor platforms) using throughput velocity analysis
3. **Dynamic KPT Adjustment**: Automatically increase Kitchen Prep Time estimates when invisible load is detected, improving delivery ETA accuracy by 30%
4. **Zero Infrastructure Cost**: Deploy without requiring new hardware, leveraging existing merchant smartphones
5. **Fraud Prevention**: Detect and flag merchants who scan empty bags prematurely to game the system

## Glossary

- **Edge_Client**: The mobile application component running on merchant's smartphone that performs local AI inference
- **Verification_Event**: A timestamped record of successful food package and receipt detection
- **Cryptographic_Payload**: SHA-256 hashed data structure containing order verification information without raw images
- **Fraud_Flag**: An indicator marking verification events as potentially fraudulent (empty bag scans, temporal anomalies)
- **Velocity_Calculator**: Backend service that calculates kitchen throughput using Little's Law
- **Baseline_Velocity**: Historical average orders per hour for a merchant during specific time windows (Vb)
- **Current_Velocity**: Recent orders per hour calculated from last 15 minutes of verifications (Vc)
- **Invisible_Load_Ratio**: Ratio of current velocity to baseline velocity (Ri = Vc / Vb), indicating kitchen congestion
- **KPT_Penalty**: Additional minutes added to Kitchen Prep Time when invisible load is detected
- **Spatial_Validation**: Verification that receipt bounding box intersects with food parcel bounding box
- **Temporal_Debouncing**: Requirement for 3 consecutive successful detections before verification succeeds
- **Fallback_Handler**: Component that provides manual override when AI inference fails
- **Ingestion_Service**: Backend microservice that receives and validates verification payloads
- **TFLite_Engine**: TensorFlow Lite inference engine running YOLOv8-nano model on mobile device
- **Bounding_Box**: Rectangular region defined by (x, y, width, height) coordinates identifying detected objects

## Requirements

### Requirement 1: Edge Camera Capture

**User Story:** As a merchant, I want the app to automatically capture camera frames without draining my phone battery, so that I can verify orders efficiently throughout my shift.

#### Acceptance Criteria

1. WHEN the verification screen is active, THE Edge_Client SHALL capture frames at exactly 3 FPS
2. WHEN a frame is captured, THE Edge_Client SHALL downscale it to 640x640 resolution before processing
3. THE Edge_Client SHALL maintain frame capture for at least 30 seconds without battery drain exceeding 2% per minute
4. WHEN camera permission is denied, THE Edge_Client SHALL display an error message and provide a button to open app settings
5. WHEN the device camera is unavailable, THE Edge_Client SHALL automatically switch to manual override mode

### Requirement 2: On-Device Object Detection

**User Story:** As a merchant, I want the app to detect food packages and receipts instantly without sending video to the cloud, so that verification works even with poor network connectivity.

#### Acceptance Criteria

1. WHEN a frame is provided, THE TFLite_Engine SHALL execute inference within 200 milliseconds
2. WHEN inference completes, THE TFLite_Engine SHALL return detections for Class 0 (Food_Parcel) and Class 1 (KOT_Receipt) with confidence scores
3. THE TFLite_Engine SHALL load the quantized YOLOv8-nano INT8 model on initialization
4. WHEN the model file is corrupted or missing, THE TFLite_Engine SHALL log an error and trigger fallback mode
5. THE TFLite_Engine SHALL leverage mobile NPU or GPU acceleration when available
6. WHEN inference fails, THE TFLite_Engine SHALL return an empty detections array without crashing

### Requirement 3: Spatial Verification

**User Story:** As a system architect, I want to ensure the receipt is physically attached to the food package, so that merchants cannot scan loose receipts on empty bags.

#### Acceptance Criteria

1. WHEN both Food_Parcel and KOT_Receipt are detected, THE Edge_Client SHALL check if their bounding boxes intersect
2. WHEN bounding boxes do not intersect, THE Edge_Client SHALL reject the verification and reset the state
3. WHEN the receipt bounding box is fully contained within the food parcel bounding box, THE Edge_Client SHALL accept the spatial validation
4. WHEN only one class is detected, THE Edge_Client SHALL reject the verification
5. THE Edge_Client SHALL use separating axis theorem for intersection calculation

### Requirement 4: Temporal Debouncing

**User Story:** As a system architect, I want to prevent motion blur and transient false positives, so that only stable detections trigger verification.

#### Acceptance Criteria

1. WHEN spatial validation succeeds, THE Edge_Client SHALL increment a consecutive success counter
2. WHEN spatial validation fails, THE Edge_Client SHALL reset the consecutive success counter to zero
3. WHEN the consecutive success counter reaches 3, THE Edge_Client SHALL trigger verification success
4. THE Edge_Client SHALL maintain verification state across frames
5. WHEN verification succeeds, THE Edge_Client SHALL reset the consecutive success counter to zero

### Requirement 5: Cryptographic Payload Generation

**User Story:** As a security engineer, I want verification payloads to be tamper-proof without transmitting sensitive image data, so that merchants cannot spoof verifications.

#### Acceptance Criteria

1. WHEN verification succeeds, THE Edge_Client SHALL generate a SHA-256 hash from OrderID, Timestamp, DeviceID, and SECRET_SALT
2. THE Edge_Client SHALL construct a JSON payload containing order_id, verified_timestamp, confidence_score, crypto_hash, and fallback_used
3. THE Edge_Client SHALL NOT include raw image data or pixel information in the payload
4. WHEN generating the hash, THE Edge_Client SHALL use the format: Hash(OrderID|Timestamp|DeviceID|SECRET_SALT)
5. THE Edge_Client SHALL pull the active Order_ID from the app UI state
6. THE Edge_Client SHALL use Unix timestamp (seconds since epoch) for verified_timestamp

### Requirement 6: Fallback Mechanisms

**User Story:** As a merchant, I want the app to help me when AI detection fails due to poor lighting or camera issues, so that I can still mark orders as ready.

#### Acceptance Criteria

1. WHEN inference fails continuously for 5 seconds, THE Fallback_Handler SHALL activate the device flashlight
2. WHEN inference fails continuously for 10 seconds, THE Fallback_Handler SHALL display a manual override button
3. WHEN the merchant clicks manual override, THE Fallback_Handler SHALL prompt for the last 4 digits of the Order ID
4. WHEN the merchant enters invalid input, THE Fallback_Handler SHALL display an error message and reject the input
5. WHEN manual override is used, THE Edge_Client SHALL set fallback_used to true in the payload
6. WHEN verification succeeds, THE Fallback_Handler SHALL stop the failure timer

### Requirement 7: Backend Payload Ingestion

**User Story:** As a backend engineer, I want to receive and validate verification payloads at high throughput, so that the system scales during peak hours.

#### Acceptance Criteria

1. WHEN a POST request is received at /api/v1/verify-order, THE Ingestion_Service SHALL validate the cryptographic hash
2. WHEN the crypto_hash is invalid, THE Ingestion_Service SHALL return HTTP 401 Unauthorized
3. WHEN the crypto_hash is valid, THE Ingestion_Service SHALL store the verification log in MongoDB
4. THE Ingestion_Service SHALL complete processing within 200 milliseconds for 95% of requests
5. THE Ingestion_Service SHALL handle at least 1000 concurrent requests without errors
6. WHEN MongoDB is unavailable, THE Ingestion_Service SHALL return HTTP 503 and queue the payload in Redis

### Requirement 8: Fraud Detection - Temporal Validation

**User Story:** As an operations manager, I want to detect merchants who scan empty bags prematurely, so that we can maintain system integrity and prevent gaming.

#### Acceptance Criteria

1. WHEN a verification event is received, THE Ingestion_Service SHALL calculate Delta = verified_timestamp - order_creation_timestamp
2. WHEN Delta is negative, THE Ingestion_Service SHALL flag the event as FRAUD_TEMPORAL_ANOMALY
3. THE Ingestion_Service SHALL query the menu database to determine minimum prep time for order items
4. WHEN Delta is less than minimum prep time, THE Ingestion_Service SHALL flag the event as FRAUD_EMPTY_BAG
5. WHEN a fraud flag is set, THE Ingestion_Service SHALL store the flag in the verification log but exclude the event from velocity calculations
6. THE Ingestion_Service SHALL use the maximum prep time among all order items as the minimum threshold
7. WHEN minimum prep time is less than 60 seconds, THE Ingestion_Service SHALL use 60 seconds as the minimum threshold

### Requirement 9: Baseline Velocity Calculation

**User Story:** As a data analyst, I want to calculate historical baseline throughput for each merchant, so that I can detect deviations indicating invisible load.

#### Acceptance Criteria

1. WHEN calculating baseline velocity, THE Velocity_Calculator SHALL query verification logs from the last 4 weeks
2. THE Velocity_Calculator SHALL filter for the same day of week and time window (e.g., Friday 7PM-8PM)
3. THE Velocity_Calculator SHALL exclude fraud-flagged verifications from the calculation
4. WHEN a merchant has fewer than 4 weeks of data, THE Velocity_Calculator SHALL use the platform-wide category average
5. THE Velocity_Calculator SHALL return orders per hour as the baseline velocity metric
6. WHEN no historical data exists, THE Velocity_Calculator SHALL return zero and set a low confidence flag

### Requirement 10: Current Velocity Calculation

**User Story:** As a data analyst, I want to calculate recent throughput velocity, so that I can compare it to baseline and detect congestion.

#### Acceptance Criteria

1. WHEN calculating current velocity, THE Velocity_Calculator SHALL query verification logs from the last 15 minutes
2. THE Velocity_Calculator SHALL exclude fraud-flagged verifications from the calculation
3. THE Velocity_Calculator SHALL extrapolate the count to an hourly rate (orders per hour)
4. WHEN no verifications exist in the window, THE Velocity_Calculator SHALL return zero
5. THE Velocity_Calculator SHALL update current velocity every 5 minutes for active merchants

### Requirement 11: Invisible Load Detection

**User Story:** As a product manager, I want to detect when a kitchen is slower than usual due to non-Zomato orders, so that we can adjust delivery estimates accordingly.

#### Acceptance Criteria

1. WHEN both baseline and current velocity are available, THE Velocity_Calculator SHALL compute Invisible_Load_Ratio = Current_Velocity / Baseline_Velocity
2. WHEN Baseline_Velocity is zero, THE Velocity_Calculator SHALL set Invisible_Load_Ratio to 1.0
3. WHEN Invisible_Load_Ratio is less than 0.5, THE Velocity_Calculator SHALL classify the kitchen as severely congested
4. WHEN Invisible_Load_Ratio is between 0.5 and 0.8, THE Velocity_Calculator SHALL classify the kitchen as moderately congested
5. WHEN Invisible_Load_Ratio is 0.8 or greater, THE Velocity_Calculator SHALL classify the kitchen as operating normally
6. THE Velocity_Calculator SHALL store the Invisible_Load_Ratio in the MerchantVelocityState collection

### Requirement 12: Dynamic KPT Penalty

**User Story:** As a delivery operations manager, I want to automatically increase Kitchen Prep Time when invisible load is detected, so that rider dispatch timing is more accurate.

#### Acceptance Criteria

1. WHEN Invisible_Load_Ratio is 0.8 or greater, THE Velocity_Calculator SHALL set KPT_Penalty to 0 minutes
2. WHEN Invisible_Load_Ratio is less than 0.5, THE Velocity_Calculator SHALL set KPT_Penalty to 15 minutes
3. WHEN Invisible_Load_Ratio is between 0.5 and 0.8, THE Velocity_Calculator SHALL calculate KPT_Penalty using linear interpolation
4. THE Velocity_Calculator SHALL clamp KPT_Penalty to a maximum of 30 minutes
5. THE Velocity_Calculator SHALL store the active KPT_Penalty in the MerchantVelocityState collection
6. WHEN KPT_Penalty is updated, THE Velocity_Calculator SHALL trigger an update to the rider dispatch system

### Requirement 13: Data Persistence

**User Story:** As a backend engineer, I want to store verification events durably, so that we can perform analytics and audit trails.

#### Acceptance Criteria

1. WHEN a verification event is validated, THE Ingestion_Service SHALL store a VerificationLog document in MongoDB
2. THE VerificationLog SHALL contain order_id, merchant_id, verified_timestamp, confidence_score, fallback_used, fraud_flag, and processing_time_ms
3. THE Ingestion_Service SHALL create a compound index on (merchant_id, verified_timestamp) for velocity queries
4. THE Ingestion_Service SHALL create an index on order_id for fraud detection lookups
5. THE Ingestion_Service SHALL set write concern to w=1 for eventual consistency
6. WHEN a MerchantVelocityState is updated, THE Velocity_Calculator SHALL use upsert to create or update the document

### Requirement 14: Security - Hash Validation

**User Story:** As a security engineer, I want to validate cryptographic hashes using constant-time comparison, so that the system is resistant to timing attacks.

#### Acceptance Criteria

1. WHEN validating a crypto_hash, THE Ingestion_Service SHALL compute the expected hash using the same algorithm as the client
2. WHEN comparing hashes, THE Ingestion_Service SHALL use constant-time comparison (XOR-based)
3. THE Ingestion_Service SHALL reject payloads where received_hash length does not equal 64 characters
4. WHEN hash validation fails, THE Ingestion_Service SHALL log a security event with device_id, IP address, and timestamp
5. WHEN a device_id has more than 5 failed hash validations in 1 hour, THE Ingestion_Service SHALL temporarily block that device_id
6. THE Ingestion_Service SHALL use the same SECRET_SALT as configured in the mobile app

### Requirement 15: Security - Replay Attack Prevention

**User Story:** As a security engineer, I want to prevent attackers from replaying captured verification payloads, so that the system cannot be gamed.

#### Acceptance Criteria

1. WHEN a verification payload is received, THE Ingestion_Service SHALL check if current_time - payload.timestamp exceeds 300 seconds
2. WHEN the timestamp is expired, THE Ingestion_Service SHALL reject the payload with HTTP 401
3. THE Ingestion_Service SHALL store processed order_ids in Redis with a TTL of 10 minutes
4. WHEN a duplicate order_id is detected within the cache window, THE Ingestion_Service SHALL reject the payload
5. THE Ingestion_Service SHALL allow legitimate retries within the 5-minute window for network failure recovery

### Requirement 16: API Rate Limiting

**User Story:** As a DevOps engineer, I want to rate limit API requests, so that the system is protected from DDoS attacks.

#### Acceptance Criteria

1. THE Ingestion_Service SHALL enforce a rate limit of 100 requests per minute per device_id
2. THE Ingestion_Service SHALL allow burst traffic of 20 requests per second
3. WHEN rate limit is exceeded, THE Ingestion_Service SHALL return HTTP 429 Too Many Requests
4. THE Ingestion_Service SHALL enforce an IP-based rate limit of 1000 requests per minute
5. WHEN more than 10% of devices hit rate limits, THE Ingestion_Service SHALL trigger a security alert

### Requirement 17: Error Handling - Network Failures

**User Story:** As a merchant, I want the app to retry failed requests automatically, so that I don't lose verification data due to poor network.

#### Acceptance Criteria

1. WHEN a POST request fails, THE Edge_Client SHALL retry with exponential backoff (1s, 2s, 4s)
2. THE Edge_Client SHALL attempt a maximum of 3 retries
3. WHEN all retries fail, THE Edge_Client SHALL store the payload in local storage
4. WHEN network connectivity is restored, THE Edge_Client SHALL send queued payloads in order
5. THE Edge_Client SHALL display a success message to the merchant even if the request is queued

### Requirement 18: Error Handling - Model Load Failure

**User Story:** As a merchant, I want the app to work even if AI inference fails, so that I can still mark orders as ready.

#### Acceptance Criteria

1. WHEN the TFLite model fails to load, THE Edge_Client SHALL log the error with device specifications
2. THE Edge_Client SHALL display a message: "AI verification unavailable, using manual mode"
3. THE Edge_Client SHALL automatically switch to manual override mode
4. WHEN manual mode is active, THE Edge_Client SHALL set fallback_used to true for all verifications
5. THE Edge_Client SHALL send an error report to the backend monitoring system

### Requirement 19: Performance - Edge Latency

**User Story:** As a merchant, I want verification to complete instantly, so that it doesn't slow down my order fulfillment workflow.

#### Acceptance Criteria

1. THE Edge_Client SHALL complete the full verification cycle (capture → inference → payload generation) within 200 milliseconds for 95% of attempts
2. WHEN inference exceeds 200ms, THE Edge_Client SHALL log performance metrics including device model and inference time
3. THE Edge_Client SHALL automatically reduce frame resolution to 480x480 if inference consistently exceeds 200ms
4. THE Edge_Client SHALL reduce FPS to 2 FPS if performance issues persist after resolution reduction

### Requirement 20: Performance - Backend Throughput

**User Story:** As a backend engineer, I want the ingestion service to handle peak traffic, so that the system doesn't fail during dinner rush hours.

#### Acceptance Criteria

1. THE Ingestion_Service SHALL process at least 2000 requests per second per worker
2. THE Ingestion_Service SHALL maintain p95 latency below 50 milliseconds for the ingestion endpoint
3. THE Ingestion_Service SHALL complete fraud detection within 30 milliseconds per verification
4. THE Ingestion_Service SHALL use async I/O for all database operations
5. THE Ingestion_Service SHALL use connection pooling with at least 100 MongoDB connections per worker

### Requirement 21: Monitoring and Observability

**User Story:** As a DevOps engineer, I want to monitor system health in real-time, so that I can detect and respond to issues quickly.

#### Acceptance Criteria

1. THE Ingestion_Service SHALL export Prometheus metrics for request count, latency, and error rate
2. THE Ingestion_Service SHALL send error events to Sentry for exception tracking
3. WHEN invalid crypto_hash rate exceeds 0.1%, THE Ingestion_Service SHALL trigger a PagerDuty alert
4. WHEN fraud_flag rate for a merchant exceeds 5%, THE Ingestion_Service SHALL send a Slack notification
5. THE Velocity_Calculator SHALL log calculation results for each merchant to application logs

### Requirement 22: Data Privacy and Compliance

**User Story:** As a compliance officer, I want to ensure the system doesn't store unnecessary PII, so that we comply with GDPR and data protection regulations.

#### Acceptance Criteria

1. THE Edge_Client SHALL NOT transmit raw camera frames or pixel data to the backend
2. THE Ingestion_Service SHALL NOT store customer names, addresses, or phone numbers in VerificationLogs
3. THE Ingestion_Service SHALL encrypt sensitive fields at rest using MongoDB encryption
4. THE Ingestion_Service SHALL use TLS 1.3 for all data in transit
5. THE Ingestion_Service SHALL retain verification logs for 90 days, then archive to Snowflake
6. WHEN a data deletion request is received, THE Ingestion_Service SHALL delete all verification logs for the specified merchant within 30 days

## Non-Functional Requirements

### NFR 1: Latency

- Edge verification cycle: <200ms p95
- Backend ingestion endpoint: <50ms p95
- Fraud detection: <30ms per verification
- Velocity calculation: <500ms per merchant (background task)

### NFR 2: Throughput

- Backend ingestion: 2000 req/sec per worker
- Concurrent connections: 1000+ per worker
- Peak load handling: 7-9 PM daily without degradation

### NFR 3: Availability

- Backend API: 99.9% uptime (8.76 hours downtime per year)
- MongoDB: 99.95% uptime via replica sets
- Graceful degradation: Manual override mode when AI fails

### NFR 4: Scalability

- Horizontal scaling: Support 100+ backend workers
- Database sharding: Shard by merchant_id for load distribution
- Model distribution: CDN for TFLite model downloads

### NFR 5: Security

- Cryptographic integrity: SHA-256 hashing for all payloads
- Timing attack resistance: Constant-time hash comparison
- Replay attack prevention: 5-minute payload expiration
- Rate limiting: 100 req/min per device, 1000 req/min per IP
- Data encryption: TLS 1.3 in transit, MongoDB encryption at rest

### NFR 6: Battery Efficiency

- Frame capture: 3 FPS (vs 30 FPS standard)
- Battery drain: <2% per minute during active verification
- Model size: <3MB (INT8 quantized)

### NFR 7: Network Efficiency

- Payload size: <200 bytes compressed (gzip)
- Zero video streaming: All inference on-device
- Retry strategy: Exponential backoff with local queue

### NFR 8: Compatibility

- Android: 8.0+ (API level 26+)
- iOS: 13.0+
- TensorFlow Lite: 2.13+
- MongoDB: 6.0+
- Python: 3.11+

### NFR 9: Maintainability

- Code coverage: 90% for core algorithms
- Property-based tests: 1000+ iterations per property
- Documentation: All public APIs documented
- Monitoring: Prometheus metrics for all critical paths

### NFR 10: Usability

- Merchant training: <5 minutes to learn verification flow
- Fallback timing: Flashlight at 5s, manual override at 10s
- Error messages: User-friendly, actionable guidance
- Success feedback: Immediate visual confirmation

## Constraints

1. **Zero New Hardware**: Must use existing merchant smartphones, no additional cameras or sensors
2. **Zero Cloud Video**: All AI inference must happen on-device, no video streaming to cloud
3. **Sub-200ms Latency**: Complete verification cycle must not slow down merchant workflow
4. **Network Resilience**: Must work in poor network conditions common in Indian kitchens
5. **Battery Efficiency**: Must not drain phone battery during 8-hour merchant shifts
6. **Model Size**: TFLite model must be <5MB for reasonable download times
7. **Backward Compatibility**: Must support Android 8.0+ and iOS 13.0+ devices
8. **Privacy Compliance**: Must comply with GDPR Article 5 (data minimization) and Article 32 (security)
9. **Fraud Prevention**: Must detect and flag at least 80% of empty bag scans
10. **Cost Efficiency**: Backend infrastructure cost must be <$0.01 per verification

## Assumptions

1. **Merchant Cooperation**: Merchants will follow instructions to attach KOT receipts to food packages
2. **Receipt Visibility**: KOT receipts are printed and physically attached to packages (not digital)
3. **Lighting Conditions**: Kitchen environments have sufficient ambient lighting for camera capture (fallback handles dark scenarios)
4. **Network Availability**: Merchants have intermittent network connectivity (3G or better)
5. **Device Capability**: Merchant smartphones have functional cameras and at least 2GB RAM
6. **Order Volume**: Average merchant processes 20-30 Zomato orders per hour during peak times
7. **Historical Data**: Merchants have been on the platform for at least 4 weeks to establish baseline velocity
8. **Menu Stability**: Menu item prep times are relatively stable and updated monthly
9. **Time Synchronization**: Device clocks are reasonably synchronized (within 5 minutes of server time)
10. **Fraud Rate**: <5% of merchants will attempt to game the system with empty bag scans
11. **Competitor Presence**: Merchants serve multiple platforms (Swiggy, direct orders, dine-in) creating invisible load
12. **Peak Hours**: Dinner rush (7-9 PM) represents 40% of daily order volume

## Success Metrics

1. **Verification Accuracy**: >95% of legitimate scans succeed within 3 seconds
2. **Fraud Detection Rate**: >80% of empty bag scans are flagged
3. **False Positive Rate**: <2% of legitimate verifications are flagged as fraud
4. **ETA Accuracy Improvement**: 30% reduction in late deliveries due to dynamic KPT adjustment
5. **Merchant Adoption**: >90% of merchants use AI verification instead of manual button
6. **System Uptime**: 99.9% availability during peak hours
7. **Latency Compliance**: 95% of verifications complete within 200ms
8. **Battery Impact**: <10% battery drain during 8-hour shift
9. **Network Resilience**: >95% of verifications succeed despite poor network (via retry and queue)
10. **Cost Efficiency**: Backend infrastructure cost <$0.01 per verification
