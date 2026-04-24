package com.bcag6.dto;

import lombok.Data;

import java.time.LocalDate;

@Data
public class CustomerDto {
    private Long id;
    private String firstName;
    private String middleName;
    private String lastName;
    private LocalDate dob;
    private String email;
}
