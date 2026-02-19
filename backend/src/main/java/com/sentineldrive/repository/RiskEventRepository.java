package com.sentineldrive.repository;

import com.sentineldrive.domain.RiskEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import org.springframework.data.domain.Pageable;

import java.time.Instant;
import java.util.List;

@Repository
public interface RiskEventRepository extends JpaRepository<RiskEvent, Long> {

    List<RiskEvent> findBySessionIdOrderByTimestampDesc(String sessionId, Pageable pageable);

    List<RiskEvent> findByTimestampBetweenOrderByTimestampDesc(Instant from, Instant to, Pageable pageable);

    List<RiskEvent> findByLevelOrderByTimestampDesc(String level, Pageable pageable);
}
