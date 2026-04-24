package com.bcag6.repository;

import com.bcag6.entity.BankAccount;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BankAccountRepository extends JpaRepository<BankAccount, Long> {

    List<BankAccount> findByCustomer_Id(Long customerId);
}
