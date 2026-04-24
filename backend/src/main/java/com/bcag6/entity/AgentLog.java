package com.bcag6.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;

@Entity
@Table(name = "agent_log")
@Getter
@Setter
@NoArgsConstructor
public class AgentLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "complaint_id", nullable = false)
    private Complaint complaint;

    @Column(name = "agent_name", nullable = false, length = 100)
    private String agentName;

    @Column(name = "action_type", nullable = false, length = 100)
    private String actionType;

    @Column(name = "input_context")
    private String inputContext;

    @Column(name = "reasoning_process")
    private String reasoningProcess;

    @Column(name = "output_context")
    private String outputContext;

    @Column(name = "created_dttm", nullable = false)
    private OffsetDateTime createdDttm;

    @PrePersist
    protected void onCreate() {
        createdDttm = OffsetDateTime.now();
    }
}
