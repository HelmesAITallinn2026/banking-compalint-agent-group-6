package com.bcag6.controller;

import com.bcag6.dto.BankAccountDto;
import com.bcag6.dto.CustomerDto;
import com.bcag6.service.BankAccountService;
import com.bcag6.service.CustomerService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/customers")
@RequiredArgsConstructor
@Tag(name = "Customers", description = "Customer data and bank accounts")
public class CustomerController {

    private final CustomerService customerService;
    private final BankAccountService bankAccountService;

    @GetMapping("/{id}")
    @Operation(summary = "Get customer by ID")
    public ResponseEntity<CustomerDto> getCustomer(@PathVariable Long id) {
        return ResponseEntity.ok(customerService.getCustomerById(id));
    }

    @GetMapping("/{id}/accounts")
    @Operation(summary = "Get bank accounts by customer ID")
    public ResponseEntity<List<BankAccountDto>> getAccounts(@PathVariable Long id) {
        return ResponseEntity.ok(bankAccountService.getAccountsByCustomerId(id));
    }
}
