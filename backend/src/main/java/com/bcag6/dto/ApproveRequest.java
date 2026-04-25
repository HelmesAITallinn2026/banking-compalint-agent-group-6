package com.bcag6.dto;

public class ApproveRequest {
    private String draftEmailSubject;
    private String draftEmailBody;

    public String getDraftEmailSubject() { return draftEmailSubject; }
    public void setDraftEmailSubject(String draftEmailSubject) { this.draftEmailSubject = draftEmailSubject; }

    public String getDraftEmailBody() { return draftEmailBody; }
    public void setDraftEmailBody(String draftEmailBody) { this.draftEmailBody = draftEmailBody; }
}
