# Panduan Setup Midtrans untuk Odoo 17

## Daftar Isi
1. [Persiapan Akun Midtrans](#persiapan-akun-midtrans)
2. [Konfigurasi di Dashboard Midtrans](#konfigurasi-di-dashboard-midtrans)
3. [Instalasi Modul di Odoo](#instalasi-modul-di-odoo)
4. [Konfigurasi Payment Provider](#konfigurasi-payment-provider)
5. [Testing](#testing)
6. [Go Live](#go-live)
7. [Troubleshooting](#troubleshooting)

## Persiapan Akun Midtrans

### 1. Daftar Akun Midtrans
1. Kunjungi [https://midtrans.com](https://midtrans.com)
2. Klik "Daftar Sekarang" atau "Sign Up"
3. Isi form pendaftaran dengan data yang valid:
   - Nama Lengkap
   - Email
   - Nomor Telepon
   - Nama Perusahaan/Toko
4. Verifikasi email yang diterima
5. Login ke dashboard Midtrans

### 2. Verifikasi Akun
1. Lengkapi profil bisnis Anda
2. Upload dokumen yang diperlukan:
   - KTP/Identitas
   - NPWP (jika ada)
   - Akta Pendirian (untuk perusahaan)
   - Surat Izin Usaha
3. Tunggu proses verifikasi (biasanya 1-3 hari kerja)

## Konfigurasi di Dashboard Midtrans

### 1. Mendapatkan API Keys

#### Untuk Sandbox (Testing):
1. Login ke [Midtrans Sandbox Dashboard](https://dashboard.sandbox.midtrans.com)
2. Pilih environment "Sandbox"
3. Pergi ke **Settings** → **Access Keys**
4. Catat informasi berikut:
   - **Merchant ID**: Contoh `G123456789`
   - **Client Key**: Contoh `SB-Mid-client-xxxxx`
   - **Server Key**: Contoh `SB-Mid-server-xxxxx`

#### Untuk Production:
1. Login ke [Midtrans Production Dashboard](https://dashboard.midtrans.com)
2. Pilih environment "Production"
3. Pergi ke **Settings** → **Access Keys**
4. Catat informasi berikut:
   - **Merchant ID**: Contoh `G123456789`
   - **Client Key**: Contoh `Mid-client-xxxxx`
   - **Server Key**: Contoh `Mid-server-xxxxx`

### 2. Konfigurasi Notification URL
1. Di dashboard Midtrans, pergi ke **Settings** → **Configuration**
2. Isi **Notification URL** dengan:
   ```
   https://yourdomain.com/payment/midtrans/notify
   ```
   Ganti `yourdomain.com` dengan domain Odoo Anda

3. Isi **Finish Redirect URL** dengan:
   ```
   https://yourdomain.com/payment/midtrans/return
   ```

4. Isi **Unfinish Redirect URL** dengan:
   ```
   https://yourdomain.com/payment/midtrans/return
   ```

5. Isi **Error Redirect URL** dengan:
   ```
   https://yourdomain.com/payment/midtrans/return
   ```

### 3. Konfigurasi Payment Methods
1. Pergi ke **Settings** → **Snap Preferences**
2. Aktifkan payment methods yang diinginkan:
   - ✅ Credit Card
   - ✅ Bank Transfer (BCA, Mandiri, BNI, BRI, Permata)
   - ✅ E-Wallet (GoPay, OVO, DANA, LinkAja, ShopeePay)
   - ✅ Over The Counter (Alfamart, Indomaret)
   - ✅ Cardless Credit (Akulaku, Kredivo)

3. Atur tampilan dan pengaturan lainnya sesuai kebutuhan

## Instalasi Modul di Odoo

### 1. Upload Modul
1. Copy folder `payment_midtrans` ke direktori addons Odoo Anda
2. Restart server Odoo
3. Update Apps List: **Apps** → **Update Apps List**

### 2. Install Modul
1. Pergi ke **Apps**
2. Hapus filter "Apps" dan cari "midtrans"
3. Klik **Install** pada modul "Payment Acquirer: Midtrans"

## Konfigurasi Payment Provider

### 1. Buat Payment Provider
1. Pergi ke **Accounting** → **Configuration** → **Payment Providers**
2. Klik **Create** atau cari provider "Midtrans" yang sudah ada
3. Isi konfigurasi berikut:

#### Tab General:
- **Name**: Midtrans
- **Provider**: Midtrans
- **State**: Test (untuk testing) atau Enabled (untuk production)
- **Company**: Pilih company Anda

#### Tab Credentials:
- **Merchant ID**: Masukkan Merchant ID dari dashboard Midtrans
- **Client Key**: Masukkan Client Key dari dashboard Midtrans
- **Server Key**: Masukkan Server Key dari dashboard Midtrans

#### Tab Configuration:
- **Payment Journal**: Pilih journal untuk payment
- **Fees**: Atur fee jika diperlukan
- **Supported Currencies**: IDR, USD, SGD, MYR

### 2. Publish Payment Provider
1. Centang **Published** untuk menampilkan di website
2. Atur **Website** jika menggunakan multi-website
3. **Save** konfigurasi

## Testing

### 1. Test dengan Sandbox
1. Pastikan menggunakan Sandbox credentials
2. State provider diset ke "Test"
3. Buat test order di website atau backend
4. Lakukan pembayaran dengan test cards:

#### Test Credit Cards:
```
Card Number: 4811 1111 1111 1114
CVV: 123
Exp Date: 01/25
```

```
Card Number: 5573 3811 1111 1115
CVV: 123
Exp Date: 01/25
```

#### Test Bank Transfer:
- Pilih bank yang tersedia
- Ikuti instruksi pembayaran
- Status akan otomatis berubah setelah simulasi pembayaran

### 2. Verifikasi Webhook
1. Cek log Odoo untuk memastikan webhook diterima
2. Verifikasi status transaksi berubah otomatis
3. Cek bahwa invoice/order statusnya terupdate

## Go Live

### 1. Persiapan Production
1. Pastikan akun Midtrans sudah terverifikasi
2. Dapatkan Production API Keys
3. Test semua payment methods di sandbox

### 2. Switch ke Production
1. Update credentials dengan Production keys
2. Ubah State provider dari "Test" ke "Enabled"
3. Update Notification URL di dashboard production
4. Test dengan transaksi kecil

### 3. Monitoring
1. Monitor log transaksi
2. Cek dashboard Midtrans untuk transaksi
3. Verifikasi settlement otomatis

## Troubleshooting

### Error: "Payment communication error"
**Penyebab**: API credentials salah atau network issue
**Solusi**:
- Verifikasi Server Key dan Client Key
- Cek koneksi internet server
- Pastikan firewall tidak memblokir Midtrans API

### Error: "Invalid signature"
**Penyebab**: Server Key tidak cocok dengan yang di dashboard
**Solusi**:
- Verifikasi Server Key di konfigurasi Odoo
- Pastikan menggunakan key yang sesuai environment (sandbox/production)

### Webhook tidak diterima
**Penyebab**: Notification URL salah atau tidak accessible
**Solusi**:
- Verifikasi Notification URL di dashboard Midtrans
- Pastikan URL dapat diakses dari internet
- Cek log server untuk error

### Transaksi pending terus
**Penyebab**: Webhook tidak sampai atau error processing
**Solusi**:
- Cek log Odoo untuk error webhook
- Manual check status via API
- Verifikasi signature key

### Payment method tidak muncul
**Penyebab**: Currency tidak didukung atau konfigurasi salah
**Solusi**:
- Pastikan currency IDR, USD, SGD, atau MYR
- Verifikasi payment methods di dashboard Midtrans
- Cek konfigurasi provider di Odoo

## Dukungan

### Midtrans Support:
- Email: support@midtrans.com
- Phone: +62 21 2212 5430
- Documentation: https://docs.midtrans.com

### Testing Tools:
- Sandbox Dashboard: https://dashboard.sandbox.midtrans.com
- API Documentation: https://api-docs.midtrans.com
- Postman Collection: Available in Midtrans docs

## Catatan Penting

1. **Keamanan**: Jangan pernah expose Server Key di client-side code
2. **Testing**: Selalu test di sandbox sebelum go live
3. **Monitoring**: Setup monitoring untuk failed transactions
4. **Backup**: Backup konfigurasi sebelum perubahan besar
5. **Update**: Keep modul dan Odoo up to date untuk security patches

## Fitur yang Didukung

✅ Snap Payment (All payment methods)
✅ Automatic status update via webhook
✅ Multi-currency (IDR, USD, SGD, MYR)
✅ Sandbox and Production environment
✅ Transaction logging
✅ Signature verification
✅ Refund support (partial)

## Fitur yang Tidak Didukung

❌ Tokenization/Saved cards
❌ Recurring payments
❌ Direct API (Core API)
❌ Manual capture
❌ Express checkout

---

*Panduan ini dibuat untuk modul Payment Midtrans Odoo 17. Untuk pertanyaan teknis, silakan hubungi developer atau Midtrans support.*