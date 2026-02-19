package com.sentineldrive.web;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sentineldrive.domain.RiskEvent;
import com.sentineldrive.repository.RiskEventRepository;
import com.sentineldrive.web.dto.RiskEventRequest;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;

@RestController
@RequestMapping("/api/v1/risk-events")
public class RiskEventController {

    private static final Logger log = LoggerFactory.getLogger(RiskEventController.class);

    private final RiskEventRepository repository;
    private final ObjectMapper objectMapper;

    public RiskEventController(RiskEventRepository repository, ObjectMapper objectMapper) {
        this.repository = repository;
        this.objectMapper = objectMapper;
    }

    /** Parse ISO-8601 timestamp from AI service (with or without trailing Z). */
    private static Instant parseTimestamp(String ts) {
        if (ts == null || ts.isBlank()) throw new IllegalArgumentException("timestamp is required");
        String s = ts.trim();
        if (!s.endsWith("Z") && !s.matches(".*[+-]\\d{2}:?\\d{2}$")) {
            s = s + "Z";
        }
        return Instant.parse(s);
    }

    @PostMapping
    public ResponseEntity<RiskEvent> create(@Valid @RequestBody RiskEventRequest request) {
        RiskEvent entity = new RiskEvent();
        entity.setLevel(request.getLevel());
        entity.setType(request.getType());
        entity.setTimestamp(parseTimestamp(request.getTimestamp()));
        entity.setSessionId(request.getSessionId());
        entity.setMessage(request.getMessage());
        if (request.getMetrics() != null && !request.getMetrics().isEmpty()) {
            try {
                entity.setMetricsJson(objectMapper.writeValueAsString(request.getMetrics()));
            } catch (JsonProcessingException e) {
                log.warn("Could not serialize metrics to JSON: {}", e.getMessage());
            }
        }
        RiskEvent saved = repository.save(entity);
        log.debug("Risk event saved: id={}, level={}, type={}", saved.getId(), saved.getLevel(), saved.getType());
        return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    }
}
