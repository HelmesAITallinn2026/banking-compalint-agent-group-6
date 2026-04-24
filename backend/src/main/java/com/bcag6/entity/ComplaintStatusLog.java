package com.bcag6.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;

@Entity
@Table(name = "complaint_status_log")
@Getter
@Setter
@NoArgsConstructor
public class ComplaintStatusLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "complaint_id", nullable = false)
    private Complaint complaint;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "status_id", nullable = false)
    private ComplaintStatus status;

    @Column(name = "updated_dttm", nullable = false)
    private OffsetDateTime updatedDttm;

    @PrePersist
    protected void onCreate() {
        if (updatedDttm == null) {
            updatedDttm = OffsetDateTime.now();
        }
    }
}
