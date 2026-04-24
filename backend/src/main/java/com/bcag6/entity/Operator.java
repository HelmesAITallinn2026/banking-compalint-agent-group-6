package com.bcag6.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;

@Entity
@Table(name = "operator")
@Getter
@Setter
@NoArgsConstructor
public class Operator {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "username", nullable = false, unique = true, length = 100)
    private String username;

    @Column(name = "email", nullable = false, unique = true, length = 255)
    private String email;

    @Enumerated(EnumType.STRING)
    @Column(name = "role", nullable = false, length = 20)
    private OperatorRole role;

    @Column(name = "created_dttm", nullable = false)
    private OffsetDateTime createdDttm;

    @PrePersist
    protected void onCreate() {
        if (createdDttm == null) {
            createdDttm = OffsetDateTime.now();
        }
    }
}
