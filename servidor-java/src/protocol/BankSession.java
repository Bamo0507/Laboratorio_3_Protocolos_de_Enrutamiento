package protocol;

import application.BankAccount;


public final class BankSession {
    public enum Phase {
        WAITING_START,
        WAITING_CARD,
        WAITING_PIN,
        WAITING_OPTION,
        WAITING_AMOUNT,
        COMPLETED
    }

    private Phase phase = Phase.WAITING_START;
    private BankAccount selectedAccount;

    public Phase getPhase() {
        return phase;
    }

    public BankAccount getSelectedAccount() {
        return selectedAccount;
    }

    public void startTransaction() {
        phase = Phase.WAITING_CARD;
    }

    public void selectAccount(BankAccount account) {
        selectedAccount = account;
        phase = Phase.WAITING_PIN;
    }

    public void acceptPin() {
        phase = Phase.WAITING_OPTION;
    }

    public void selectWithdrawal() {
        phase = Phase.WAITING_AMOUNT;
    }

    public void completeOperation() {
        phase = Phase.COMPLETED;
    }
}
