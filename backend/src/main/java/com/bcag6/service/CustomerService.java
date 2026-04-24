package com.bcag6.service;

import com.bcag6.dto.CustomerDto;
import com.bcag6.entity.Customer;
import com.bcag6.exception.ResourceNotFoundException;
import com.bcag6.mapper.CustomerMapper;
import com.bcag6.repository.CustomerRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class CustomerService {

    private final CustomerRepository customerRepository;
    private final CustomerMapper customerMapper;

    @Transactional(readOnly = true)
    public CustomerDto getCustomerById(Long id) {
        Customer customer = customerRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Customer not found with id: " + id));
        return customerMapper.toDto(customer);
    }
}
