# Payment Midtrans for Odoo 17

Modul integrasi payment gateway Midtrans untuk Odoo 17 yang memungkinkan penerimaan pembayaran online melalui berbagai metode pembayaran yang didukung Midtrans.

## Fitur

- ✅ **Snap Payment Integration** - Menggunakan Midtrans Snap untuk UI pembayaran yang responsif
- ✅ **Multiple Payment Methods** - Credit Card, Bank Transfer, E-Wallet, Over The Counter, Cardless Credit
- ✅ **Multi Currency** - Mendukung IDR, USD, SGD, MYR
- ✅ **Automatic Status Update** - Webhook otomatis untuk update status transaksi
- ✅ **Sandbox & Production** - Environment testing dan production
- ✅ **Security** - Signature verification untuk keamanan webhook
- ✅ **Transaction Logging** - Log lengkap untuk monitoring dan debugging

## Metode Pembayaran yang Didukung

### Credit Card
- Visa, Mastercard, JCB, Amex
- 3D Secure authentication
- Installment (untuk kartu tertentu)

### Bank Transfer
- BCA Virtual Account
- Mandiri Bill Payment
- BNI Virtual Account  
- BRI Virtual Account
- Permata Virtual Account
- CIMB Niaga Virtual Account

### E-Wallet
- GoPay
- OVO
- DANA
- LinkAja
- ShopeePay

### Over The Counter
- Alfamart
- Indomaret

### Cardless Credit
- Akulaku PayLater
- Kredivo

## Instalasi

1. Copy folder `payment_midtrans` ke direktori addons Odoo
2. Restart Odoo server
3. Update Apps List
4. Install modul "Payment Acquirer: Midtrans"

## Konfigurasi

### 1. Setup Akun Midtrans
- Daftar di [Midtrans](https://midtrans.com)
- Verifikasi akun bisnis
- Dapatkan API credentials (Merchant ID, Client Key, Server Key)

### 2. Konfigurasi di Odoo
1. Pergi ke **Accounting** → **Configuration** → **Payment Providers**
2. Buat atau edit provider "Midtrans"
3. Isi credentials dari dashboard Midtrans
4. Set notification URL di dashboard Midtrans: `https://yourdomain.com/payment/midtrans/notify`

## Testing

Gunakan Sandbox environment untuk testing:
- Sandbox Dashboard: https://dashboard.sandbox.midtrans.com
- Test cards tersedia di dokumentasi Midtrans
- Semua transaksi di sandbox adalah simulasi

## Production

1. Verifikasi akun Midtrans
2. Dapatkan Production credentials
3. Update konfigurasi dengan Production keys
4. Ubah state provider ke "Enabled"

## Struktur Modul

```
payment_midtrans/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── models/
│   ├── __init__.py
│   ├── payment_provider.py
│   └── payment_transaction.py
├── views/
│   ├── payment_midtrans_templates.xml
│   └── payment_provider_views.xml
├── data/
│   └── payment_provider_data.xml
├── security/
│   └── ir.model.access.csv
└── static/
    └── src/
        └── js/
            └── payment_form.js
```

## API Endpoints

- **Notification URL**: `/payment/midtrans/notify` - Webhook dari Midtrans
- **Return URL**: `/payment/midtrans/return` - Redirect setelah pembayaran
- **Test URL**: `/payment/midtrans/test` - Test endpoint

## Keamanan

- Server Key disimpan dengan enkripsi
- Signature verification untuk semua webhook
- HTTPS required untuk production
- Input validation dan sanitization

## Troubleshooting

### Payment tidak muncul
- Cek currency yang didukung (IDR, USD, SGD, MYR)
- Verifikasi konfigurasi provider
- Pastikan provider dalam state "Test" atau "Enabled"

### Webhook tidak diterima
- Verifikasi Notification URL di dashboard Midtrans
- Pastikan URL dapat diakses dari internet
- Cek firewall dan security settings

### Transaksi gagal
- Cek log Odoo untuk error details
- Verifikasi API credentials
- Pastikan koneksi internet server

## Dukungan

- **Dokumentasi Midtrans**: https://docs.midtrans.com
- **API Documentation**: https://api-docs.midtrans.com
- **Support Email**: support@midtrans.com

## Changelog

### Version 1.0.0
- Initial release
- Snap payment integration
- Multi payment methods support
- Webhook handling
- Multi currency support

## License

LGPL-3

## Kontributor

- Developer: [Your Name]
- Company: [Your Company]

---

Untuk panduan setup lengkap, lihat file `MIDTRANS_SETUP_GUIDE.md`