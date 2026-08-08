package application;

import java.util.ArrayList;
import java.util.List;


public final class BankService {
    private final List<BankAccount> bankAccounts;

    public BankService() {
        bankAccounts = new ArrayList<>();

        bankAccounts.add(
            new BankAccount(
                "123456",
                "Bryan Martinez",
                "0507",
                10000
            )
        );
        bankAccounts.add(
            new BankAccount(
                "098765",
                "Adriana Palacios",
                "0607",
                10000
            )
        );
    }

    public BankAccount findAccount(String cardNumber) {
        for (BankAccount bankAccount : bankAccounts) {
            if (bankAccount.getCardNumber().equals(cardNumber)) {
                return bankAccount;
            }
        }

        return null;
    }

    public boolean validatePin(
        BankAccount bankAccount,
        String providedPin
    ) {
        return bankAccount.isPinCorrect(providedPin);
    }

    public int getBalance(BankAccount bankAccount) {
        return bankAccount.getBalance();
    }

    public boolean hasSufficientFunds(
        BankAccount bankAccount,
        int withdrawalAmount
    ) {
        return bankAccount.hasSufficientFunds(withdrawalAmount);
    }

    public void withdraw(
        BankAccount bankAccount,
        int withdrawalAmount
    ) {
        bankAccount.withdraw(withdrawalAmount);
    }
}
