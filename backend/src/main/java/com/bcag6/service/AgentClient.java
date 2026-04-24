package com.bcag6.service;

import com.bcag6.dto.GenerateDraftRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Service
@Slf4j
public class AgentClient {

    private final RestTemplate restTemplate;
    private final String agentBaseUrl;

    public AgentClient(@Value("${app.agent.base-url:http://localhost:8000}") String agentBaseUrl) {
        this.restTemplate = new RestTemplate();
        this.agentBaseUrl = agentBaseUrl;
    }

    @Async
    public void triggerProcessing(Long complaintId) {
        String url = agentBaseUrl + "/process/" + complaintId;
        try {
            restTemplate.postForEntity(url, null, String.class);
            log.info("Agent processing triggered for complaintId={}", complaintId);
        } catch (Exception e) {
            log.error("Failed to trigger agent processing for complaintId={}: {}", complaintId, e.getMessage());
        }
    }

    @Async
    public void triggerDraftGeneration(Long complaintId, GenerateDraftRequest request) {
        String url = agentBaseUrl + "/draft-response";
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            Map<String, Object> body = Map.of(
                "complaint_id", complaintId.toString(),
                "decision", request.getDecision() != null ? request.getDecision() : "POSITIVE",
                "refusal_reason", request.getRefusalReason() != null ? request.getRefusalReason() : "",
                "clarification_message", request.getClarificationMessage() != null ? request.getClarificationMessage() : ""
            );
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
            restTemplate.postForEntity(url, entity, String.class);
            log.info("Agent draft generation triggered for complaintId={}", complaintId);
        } catch (Exception e) {
            log.error("Failed to trigger agent draft for complaintId={}: {}", complaintId, e.getMessage());
        }
    }
}
