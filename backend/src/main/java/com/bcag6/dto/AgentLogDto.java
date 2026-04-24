package com.bcag6.dto;

import lombok.Data;

import java.time.OffsetDateTime;

@Data
public class AgentLogDto {
    private Long id;
    private String agentName;
    private String actionType;
    private String inputContext;
    private String reasoningProcess;
    private String outputContext;
    private OffsetDateTime createdDttm;
}
