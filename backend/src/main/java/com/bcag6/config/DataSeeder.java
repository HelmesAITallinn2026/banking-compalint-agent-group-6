package com.bcag6.config;

import com.bcag6.entity.*;
import com.bcag6.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

/**
 * Seeds demo complaints (one per pipeline status) when the complaint table is empty.
 * Skipped in test profile.
 */
@Component
@Profile("!test")
@RequiredArgsConstructor
@Slf4j
public class DataSeeder implements ApplicationRunner {

    private final CustomerRepository customerRepository;
    private final ComplaintRepository complaintRepository;
    private final ComplaintStatusRepository complaintStatusRepository;
    private final ComplaintStatusLogRepository statusLogRepository;
    private final AgentLogRepository agentLogRepository;
    private final BankAccountRepository bankAccountRepository;

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        if (complaintRepository.count() > 0) {
            log.info("Complaints already exist — skipping demo seed.");
            return;
        }
        if (complaintStatusRepository.count() == 0) {
            log.warn("No complaint statuses found — skipping demo seed. Run the DB schema/seed scripts first.");
            return;
        }

        log.info("Seeding demo complaints...");

        // Resolve statuses by ID
        Map<Integer, ComplaintStatus> statuses = new java.util.HashMap<>();
        complaintStatusRepository.findAll().forEach(s -> statuses.put(s.getId(), s));

        // Ensure demo customers exist
        Customer janeSmith = findOrCreateCustomer("Jane", null, "Smith", LocalDate.of(1985, 8, 23), "jane.smith@example.com");
        Customer mariaGarcia = findOrCreateCustomer("Maria", "L", "Garcia", LocalDate.of(1992, 3, 14), "maria.garcia@example.com");
        Customer robertJohnson = findOrCreateCustomer("Robert", null, "Johnson", LocalDate.of(1978, 11, 2), "robert.johnson@example.com");
        Customer emilychen = findOrCreateCustomer("Emily", "R", "Chen", LocalDate.of(1995, 6, 30), "emily.chen@example.com");

        // Ensure John Doe exists (may already be seeded by SQL scripts)
        Customer johnDoe = findOrCreateCustomer("John", "A", "Doe", LocalDate.of(1990, 5, 12), "john.doe@example.com");

        // Bank accounts
        ensureBankAccount(janeSmith, "EE382200221020145685", "EUR", new BigDecimal("8750.00"), AccountType.CHECKING);
        ensureBankAccount(mariaGarcia, "EE501010220012345678", "EUR", new BigDecimal("3200.50"), AccountType.SAVINGS);
        ensureBankAccount(robertJohnson, "EE701700017000123456", "EUR", new BigDecimal("15400.00"), AccountType.CHECKING);
        ensureBankAccount(emilychen, "EE601400017000234567", "EUR", new BigDecimal("920.75"), AccountType.CREDIT);

        OffsetDateTime now = OffsetDateTime.now();

        // ── Complaint 1: Submitted ──────────────────────────────────
        Complaint c1 = createComplaint(janeSmith, statuses.get(1),
                "Unauthorized ATM withdrawal",
                "I noticed an ATM withdrawal of 200 EUR on 2026-04-20 that I did not make. My card was in my possession the whole time. Please investigate and reverse this transaction.",
                now.minusHours(2));
        writeStatusLogs(c1, statuses, 1, now.minusHours(2));

        // ── Complaint 2: Data Extracted ─────────────────────────────
        Complaint c2 = createComplaint(mariaGarcia, statuses.get(2),
                "Double charge on credit card",
                "I was charged twice for a purchase at Electronics Store on 2026-04-18. The amount of 149.99 EUR appeared two times on my statement. I only made one purchase.",
                now.minusHours(5));
        c2.setExtractedData("{\"merchant\": \"Electronics Store\", \"amount\": 149.99, \"currency\": \"EUR\", \"transaction_date\": \"2026-04-18\", \"occurrences\": 2}");
        complaintRepository.save(c2);
        writeStatusLogs(c2, statuses, 2, now.minusHours(5));
        writeAgentLog(c2, "extraction_agent", "extract_data",
                "Parsed complaint text. Identified merchant name, amount, currency, date, and duplicate charge pattern.");

        // ── Complaint 3: Categorised ────────────────────────────────
        Complaint c3 = createComplaint(robertJohnson, statuses.get(3),
                "Loan interest rate discrepancy",
                "My loan agreement states a fixed interest rate of 3.5%, but my latest statement shows 4.1%. This has been going on for two months.",
                now.minusDays(1));
        c3.setExtractedData("{\"loan_type\": \"personal\", \"agreed_rate\": 3.5, \"charged_rate\": 4.1, \"duration_months\": 2}");
        c3.setCategory("Loan / Interest Rate");
        complaintRepository.save(c3);
        writeStatusLogs(c3, statuses, 3, now.minusDays(1));
        writeAgentLog(c3, "extraction_agent", "extract_data",
                "Parsed complaint text. Identified loan type, agreed vs charged interest rates, and duration.");
        writeAgentLog(c3, "categorization_agent", "categorize",
                "Complaint involves loan interest rate mismatch. Mapped to Loan / Interest Rate category.");

        // ── Complaint 4: Decision Recommendation Created ────────────
        Complaint c4 = createComplaint(johnDoe, statuses.get(4),
                "Failed wire transfer with fee charged",
                "I initiated a wire transfer of 5000 EUR on 2026-04-15. The transfer failed but I was still charged a 25 EUR fee.",
                now.minusDays(2));
        c4.setExtractedData("{\"transfer_amount\": 5000, \"currency\": \"EUR\", \"transfer_date\": \"2026-04-15\", \"fee_charged\": 25}");
        c4.setCategory("Wire Transfer / Fees");
        c4.setRecommendation("POSITIVE");
        c4.setRecommendationReasoning("Fee charged for failed transfer due to SWIFT timeout. Bank policy supports refund. Recommend full refund of the 25 EUR fee.");
        complaintRepository.save(c4);
        writeStatusLogs(c4, statuses, 4, now.minusDays(2));
        writeAgentLog(c4, "extraction_agent", "extract_data",
                "Parsed wire transfer details including amount, destination, date, and fee.");
        writeAgentLog(c4, "categorization_agent", "categorize",
                "Complaint involves failed wire transfer and associated fee. Mapped to Wire Transfer / Fees.");
        writeAgentLog(c4, "recommendation_agent", "recommend",
                "Fee charged for failed transfer due to SWIFT timeout. Bank policy supports refund. Recommend POSITIVE.");

        // ── Complaint 5: Draft Created ──────────────────────────────
        Complaint c5 = createComplaint(emilychen, statuses.get(5),
                "Overdraft fee dispute",
                "I was charged a 35 EUR overdraft fee on 2026-04-10. I had set up a salary deposit that was delayed by one day due to a bank holiday.",
                now.minusDays(3));
        c5.setExtractedData("{\"fee_amount\": 35, \"currency\": \"EUR\", \"fee_date\": \"2026-04-10\"}");
        c5.setCategory("Account Fees / Overdraft");
        c5.setRecommendation("POSITIVE");
        c5.setRecommendationReasoning("First-time overdraft caused by bank holiday delay. Policy allows waiver. Recommend waiving the 35 EUR fee.");
        c5.setDraftEmailSubject("Re: Overdraft Fee Dispute — Resolution");
        c5.setDraftEmailBody("Dear Emily,\n\nThank you for contacting us regarding the overdraft fee charged to your account on 10 April 2026.\n\nWe have reviewed your case and can confirm that the fee was triggered by a one-day delay in your salary deposit caused by a bank holiday. As this is a first-time occurrence and was outside your control, we have decided to waive the 35 EUR overdraft fee.\n\nThe credit will appear on your account within 1–2 business days.\n\nKind regards,\nHelmes Bank Customer Support");
        complaintRepository.save(c5);
        writeStatusLogs(c5, statuses, 5, now.minusDays(3));
        writeAgentLog(c5, "extraction_agent", "extract_data",
                "Parsed overdraft fee details including amount, date, and salary deposit delay.");
        writeAgentLog(c5, "categorization_agent", "categorize",
                "Complaint involves overdraft fee. Mapped to Account Fees / Overdraft.");
        writeAgentLog(c5, "recommendation_agent", "recommend",
                "First-time overdraft caused by bank holiday delay. Policy allows waiver. Recommend POSITIVE.");
        writeAgentLog(c5, "drafting_agent", "draft_response",
                "Generated customer-facing email confirming fee waiver with expected timeline.");

        // ── Complaint 6: Completed ──────────────────────────────────
        Complaint c6 = createComplaint(janeSmith, statuses.get(6),
                "Debit card fraud",
                "My debit card was used for three online purchases totalling 450 EUR on 2026-04-05 that I did not authorize. I have since blocked my card.",
                now.minusDays(5));
        c6.setExtractedData("{\"transactions\": [{\"merchant\": \"OnlineShop A\", \"amount\": 150}, {\"merchant\": \"OnlineShop B\", \"amount\": 200}, {\"merchant\": \"OnlineShop C\", \"amount\": 100}], \"total\": 450, \"currency\": \"EUR\"}");
        c6.setCategory("Card Fraud / Unauthorized Transactions");
        c6.setRecommendation("POSITIVE");
        c6.setRecommendationReasoning("Verified fraud pattern. Bank fraud policy mandates reimbursement within 60 days. Recommend full refund of 450 EUR.");
        c6.setDraftEmailSubject("Re: Debit Card Fraud Report — Resolution");
        c6.setDraftEmailBody("Dear Jane,\n\nThank you for reporting the unauthorized transactions on your debit card.\n\nAfter a thorough investigation, we have confirmed that the three transactions totalling 450 EUR were fraudulent. We have processed a full refund to your account.\n\nYour new debit card has been dispatched and should arrive within 3–5 business days.\n\nKind regards,\nHelmes Bank Customer Support");
        c6.setResolvedDttm(now.minusDays(1));
        complaintRepository.save(c6);
        writeStatusLogs(c6, statuses, 6, now.minusDays(5));
        writeAgentLog(c6, "extraction_agent", "extract_data",
                "Parsed fraud report. Identified three unauthorized transactions, total amount, and card block status.");
        writeAgentLog(c6, "categorization_agent", "categorize",
                "Complaint involves unauthorized card transactions. Mapped to Card Fraud / Unauthorized Transactions.");
        writeAgentLog(c6, "recommendation_agent", "recommend",
                "Verified fraud pattern. Bank fraud policy mandates reimbursement within 60 days. Recommend POSITIVE.");
        writeAgentLog(c6, "drafting_agent", "draft_response",
                "Generated resolution email confirming full refund and new card dispatch.");

        log.info("Seeded 6 demo complaints (statuses 1–6).");
    }

    // ── Helpers ──────────────────────────────────────────────────────

    private Customer findOrCreateCustomer(String first, String middle, String last, LocalDate dob, String email) {
        return customerRepository.findAll().stream()
                .filter(c -> c.getEmail().equals(email))
                .findFirst()
                .orElseGet(() -> {
                    Customer c = new Customer();
                    c.setFirstName(first);
                    c.setMiddleName(middle);
                    c.setLastName(last);
                    c.setDob(dob);
                    c.setEmail(email);
                    return customerRepository.save(c);
                });
    }

    private void ensureBankAccount(Customer customer, String accountNumber, String currency, BigDecimal balance, AccountType type) {
        boolean exists = bankAccountRepository.findByCustomer_Id(customer.getId()).stream()
                .anyMatch(a -> a.getAccountNumber().equals(accountNumber));
        if (!exists) {
            BankAccount account = new BankAccount();
            account.setCustomer(customer);
            account.setAccountNumber(accountNumber);
            account.setCurrency(currency);
            account.setBalance(balance);
            account.setAccountType(type);
            bankAccountRepository.save(account);
        }
    }

    private Complaint createComplaint(Customer customer, ComplaintStatus status, String subject, String text, OffsetDateTime createdAt) {
        Complaint c = new Complaint();
        c.setCustomer(customer);
        c.setStatus(status);
        c.setSubject(subject);
        c.setText(text);
        c.setCreatedDttm(createdAt);
        c.setUpdatedDttm(createdAt);
        return complaintRepository.save(c);
    }

    private void writeStatusLogs(Complaint complaint, Map<Integer, ComplaintStatus> statuses, int upToStatusId, OffsetDateTime baseTime) {
        for (int i = 1; i <= upToStatusId; i++) {
            ComplaintStatus status = statuses.get(i);
            if (status == null) continue;
            ComplaintStatusLog log = new ComplaintStatusLog();
            log.setComplaint(complaint);
            log.setStatus(status);
            log.setUpdatedDttm(baseTime.plusHours((long) i * 2));
            statusLogRepository.save(log);
        }
    }

    private void writeAgentLog(Complaint complaint, String agentName, String actionType, String reasoning) {
        AgentLog entry = new AgentLog();
        entry.setComplaint(complaint);
        entry.setAgentName(agentName);
        entry.setActionType(actionType);
        entry.setReasoningProcess(reasoning);
        agentLogRepository.save(entry);
    }
}
