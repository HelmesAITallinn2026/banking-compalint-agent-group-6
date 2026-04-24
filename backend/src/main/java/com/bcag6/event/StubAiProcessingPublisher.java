package com.bcag6.event;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class StubAiProcessingPublisher implements AiProcessingPublisher {

    @Override
    public void publish(Long complaintId) {
        log.info("[AI-STUB] AI processing triggered for complaintId={}", complaintId);
    }
}
