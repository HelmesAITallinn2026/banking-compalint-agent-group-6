package com.bcag6.dto;

import lombok.Data;

import java.time.OffsetDateTime;
import java.util.List;

@Data
public class AgentDetailDto {
    private Long id;
    private String firstName;
    private String lastName;
    private String subject;
    private String text;
    private String refusalReason;
    private Integer statusId;
    private String status;
    private String extractedData;
    private String category;
    private String recommendation;
    private String recommendationReasoning;
    private String draftEmailBody;
    private OffsetDateTime createdDttm;
    private OffsetDateTime updatedDttm;
    private List<AgentAttachmentDto> attachments;

    @Data
    public static class AgentAttachmentDto {
        private Long id;
        private String fileName;
        private String mimeType;
        private Long fileSize;
    }
}
