/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PaymentForm } from "@payment/js/payment_form";

PaymentForm.include({
    
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Prepare the inline form of Midtrans for direct payment.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} code - The code of the payment option's provider.
     * @param {number} paymentOptionId - The id of the payment option handling the transaction.
     * @param {string} flow - The online payment flow of the transaction.
     * @return {void}
     */
    _prepareInlineForm: function (code, paymentOptionId, flow) {
        if (code !== 'midtrans') {
            this._super(...arguments);
            return;
        }

        // Midtrans uses redirect flow, no inline form needed
        this._setPaymentFlow('redirect');
    },

    /**
     * Process the payment with Midtrans.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} code - The code of the payment option's provider.
     * @param {number} paymentOptionId - The id of the payment option handling the transaction.
     * @param {string} flow - The online payment flow of the transaction.
     * @return {void}
     */
    _processPayment: function (code, paymentOptionId, flow) {
        if (code !== 'midtrans') {
            this._super(...arguments);
            return;
        }

        // For Midtrans, we redirect to the payment processing page
        this._redirectToProcessing();
    },

    /**
     * Redirect to the payment processing page.
     *
     * @private
     * @return {void}
     */
    _redirectToProcessing: function () {
        window.location = '/payment/process';
    },

});

// Additional Midtrans specific functions
window.MidtransPayment = {
    
    /**
     * Initialize Snap payment
     * @param {string} snapToken - Snap token from server
     * @param {string} clientKey - Client key from Midtrans
     * @param {boolean} isProduction - Whether using production environment
     */
    initSnap: function(snapToken, clientKey, isProduction) {
        const snapUrl = isProduction ? 
            'https://app.midtrans.com/snap/snap.js' : 
            'https://app.sandbox.midtrans.com/snap/snap.js';
            
        // Load Snap.js
        const script = document.createElement('script');
        script.src = snapUrl;
        script.setAttribute('data-client-key', clientKey);
        document.head.appendChild(script);
        
        script.onload = function() {
            // Snap is ready
            console.log('Midtrans Snap loaded successfully');
        };
    },
    
    /**
     * Pay with Snap
     * @param {string} snapToken - Snap token
     * @param {Object} callbacks - Success, pending, error callbacks
     */
    payWithSnap: function(snapToken, callbacks) {
        if (typeof snap === 'undefined') {
            console.error('Snap.js not loaded');
            return;
        }
        
        snap.pay(snapToken, {
            onSuccess: callbacks.onSuccess || function(result) {
                console.log('Payment success:', result);
                window.location.href = '/payment/status';
            },
            onPending: callbacks.onPending || function(result) {
                console.log('Payment pending:', result);
                window.location.href = '/payment/status';
            },
            onError: callbacks.onError || function(result) {
                console.log('Payment error:', result);
                window.location.href = '/payment/status?error=1';
            },
            onClose: callbacks.onClose || function() {
                console.log('Payment popup closed');
            }
        });
    }
};