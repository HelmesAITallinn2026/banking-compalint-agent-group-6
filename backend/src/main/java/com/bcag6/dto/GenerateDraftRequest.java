package com.bcag6.dto;

import lombok.Data;

@Data
public class GenerateDraftRequest {
    private String decision;
    private String refusalReason;
    private String clarificationMessage;
}
