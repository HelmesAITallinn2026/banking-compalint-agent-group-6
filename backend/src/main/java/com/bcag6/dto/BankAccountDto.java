package com.bcag6.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

@Data
public class BankAccountDto {
    private Long id;
    private Long customerId;
    private String accountNumber;
    private String currency;
    private BigDecimal balance;
    private String accountType;
    private OffsetDateTime createdDttm;
}
