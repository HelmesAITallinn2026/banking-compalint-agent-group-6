package com.bcag6.event;

public interface AiProcessingPublisher {

    /**
     * Publishes a complaint-created event to trigger AI processing.
     * The stub implementation logs the event; replace with a real publisher
     * (e.g. Spring ApplicationEvent, Kafka, HTTP call) when the AI service is ready.
     */
    void publish(Long complaintId);
}
