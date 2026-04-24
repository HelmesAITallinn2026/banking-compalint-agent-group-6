package com.bcag6.repository;

import com.bcag6.entity.AgentLog;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface AgentLogRepository extends JpaRepository<AgentLog, Long> {
    List<AgentLog> findByComplaintIdOrderByCreatedDttmAsc(Long complaintId);
}
