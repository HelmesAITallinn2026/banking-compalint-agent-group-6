package com.bcag6.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;

@Entity
@Table(name = "complaint")
@Getter
@Setter
@NoArgsConstructor
public class Complaint {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "status_id", nullable = false)
    private ComplaintStatus status;

    @Column(name = "created_dttm", nullable = false)
    private OffsetDateTime createdDttm;

    @Column(name = "updated_dttm", nullable = false)
    private OffsetDateTime updatedDttm;

    @Column(name = "resolved_dttm")
    private OffsetDateTime resolvedDttm;

    @Column(name = "subject", nullable = false, length = 255)
    private String subject;

    @Column(name = "text", nullable = false)
    private String text;

    @Column(name = "draft_email_subject", length = 255)
    private String draftEmailSubject;

    @Column(name = "draft_email_body")
    private String draftEmailBody;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "operator_id")
    private Operator operator;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "refusal_reason_id")
    private RefusalReason refusalReason;

    @PrePersist
    protected void onCreate() {
        OffsetDateTime now = OffsetDateTime.now();
        createdDttm = now;
        updatedDttm = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedDttm = OffsetDateTime.now();
    }
}
