package com.bcag6.dto;

import lombok.Data;

@Data
public class AgentUpdateRequest {
    private Integer statusId;
    private String extractedData;
    private String category;
    private String recommendation;
    private String recommendationReasoning;
    private String draftEmailSubject;
    private String draftEmailBody;
}
