package com.bcag6.event;

import com.bcag6.service.AgentClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class AgentHttpPublisher implements AiProcessingPublisher {

    private final AgentClient agentClient;

    @Override
    public void publish(Long complaintId) {
        log.info("Triggering agent processing for complaintId={}", complaintId);
        agentClient.triggerProcessing(complaintId);
    }
}
