package com.bcag6.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class EmailService {

    @Value("${app.email.enabled:false}")
    private boolean emailEnabled;

    /**
     * Sends the draft email to the customer.
     * When {@code app.email.enabled=false} (default), the email is logged instead of sent.
     * Set {@code app.email.enabled=true} and configure {@code spring.mail.*} for real SMTP.
     */
    public void sendDraftEmail(String toAddress, String subject, String body) {
        if (!emailEnabled) {
            log.info("[EMAIL-STUB] Email sending disabled — to={} subject={}", toAddress, subject);
            log.debug("[EMAIL-STUB] Body: {}", body);
            return;
        }
        // TODO: inject JavaMailSender and send via SMTP when email is enabled
        log.warn("[EMAIL] app.email.enabled=true but JavaMailSender is not configured.");
    }
}
