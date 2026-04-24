package com.bcag6.service;

import com.bcag6.dto.AgentLogDto;
import com.bcag6.entity.AgentLog;
import com.bcag6.entity.Complaint;
import com.bcag6.exception.ResourceNotFoundException;
import com.bcag6.repository.AgentLogRepository;
import com.bcag6.repository.ComplaintRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class AgentLogService {

    private final AgentLogRepository agentLogRepository;
    private final ComplaintRepository complaintRepository;

    @Transactional
    public AgentLogDto createLog(Long complaintId, AgentLogDto dto) {
        Complaint complaint = complaintRepository.findById(complaintId)
            .orElseThrow(() -> new ResourceNotFoundException("Complaint not found with id: " + complaintId));

        AgentLog log = new AgentLog();
        log.setComplaint(complaint);
        log.setAgentName(dto.getAgentName());
        log.setActionType(dto.getActionType());
        log.setInputContext(dto.getInputContext());
        log.setReasoningProcess(dto.getReasoningProcess());
        log.setOutputContext(dto.getOutputContext());
        AgentLog saved = agentLogRepository.save(log);

        return toDto(saved);
    }

    @Transactional(readOnly = true)
    public List<AgentLogDto> getLogsByComplaintId(Long complaintId) {
        return agentLogRepository.findByComplaintIdOrderByCreatedDttmAsc(complaintId)
            .stream().map(this::toDto).toList();
    }

    private AgentLogDto toDto(AgentLog log) {
        AgentLogDto dto = new AgentLogDto();
        dto.setId(log.getId());
        dto.setAgentName(log.getAgentName());
        dto.setActionType(log.getActionType());
        dto.setInputContext(log.getInputContext());
        dto.setReasoningProcess(log.getReasoningProcess());
        dto.setOutputContext(log.getOutputContext());
        dto.setCreatedDttm(log.getCreatedDttm());
        return dto;
    }
}
