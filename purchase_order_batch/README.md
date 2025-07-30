# Purchase Order Batch Module

Modul Odoo untuk menggabungkan beberapa Purchase Order (PO) menjadi 1 batch, mirip seperti fitur batch transfer di Odoo.

## Fitur Utama

### 1. Batch Management
- **Membuat Batch**: Gabungkan beberapa PO ke dalam satu batch
- **Status Tracking**: Pantau status batch (Draft, Confirmed, Processing, Done, Cancelled)
- **Batch Processing**: Proses semua PO dalam batch secara bersamaan
- **Batch Approval**: Approve semua PO dalam batch sekaligus

### 2. Purchase Order Integration
- **Batch Field**: Field batch_id pada Purchase Order
- **Batch Status**: Lihat status batch dari PO
- **Batch Actions**: Action untuk menambah/menghapus PO dari batch
- **Batch Filters**: Filter PO berdasarkan status batch

### 3. Wizard Interface
- **Create Batch Wizard**: Wizard untuk membuat batch baru
- **Add to Batch Wizard**: Wizard untuk menambah PO ke batch existing
- **Filter Options**: Filter berdasarkan vendor, tanggal, dll

### 4. Views & Reports
- **Kanban View**: Tampilan kanban untuk batch management
- **Tree View**: List view dengan informasi batch
- **Form View**: Detail view dengan notebook tabs
- **Search & Filters**: Pencarian dan filter yang lengkap

## Cara Penggunaan

### 1. Membuat Batch Baru

#### Dari Menu
1. Buka **Purchase > Purchase Batches > Create Batch**
2. Pilih Purchase Orders yang akan dimasukkan ke batch
3. Isi nama batch (opsional) dan notes
4. Klik **Create Batch**

#### Dari Purchase Order List
1. Pilih beberapa Purchase Orders (state: draft, sent, to approve)
2. Klik **Action > Create Batch**
3. Batch akan dibuat otomatis dengan PO yang dipilih

### 2. Mengelola Batch

#### Confirm Batch
- Status: Draft → Confirmed
- Validasi semua PO dalam batch
- Batch siap untuk diproses

#### Process Batch
- Status: Confirmed → Processing → Done
- Confirm/approve semua PO dalam batch
- Proses otomatis sesuai state masing-masing PO

#### Cancel Batch
- Batalkan batch (hanya jika belum Done)
- PO tetap ada, hanya keluar dari batch

### 3. Menambah/Menghapus PO

#### Menambah PO ke Batch
- Dari batch form: edit field purchase_order_ids
- Menggunakan "Add to Batch Wizard"

#### Menghapus PO dari Batch
- Dari batch form: hapus dari list PO
- Dari PO: Action > Remove from Batch

## State Flow

```
Draft → Confirmed → Processing → Done
  ↓         ↓
Cancelled ←─┘
  ↓
Draft (Reset)
```

### State Descriptions
- **Draft**: Batch baru dibuat, bisa edit PO
- **Confirmed**: Batch dikonfirmasi, PO terkunci
- **Processing**: Sedang memproses PO dalam batch
- **Done**: Semua PO dalam batch berhasil diproses
- **Cancelled**: Batch dibatalkan

## Validasi & Constraints

### Purchase Order Validation
- Hanya PO dengan state 'draft', 'sent', 'to approve' yang bisa di-batch
- PO yang sudah dalam batch tidak bisa ditambah ke batch lain
- PO dalam batch confirmed/processing tidak bisa diubah manual

### Batch Validation
- Batch tanpa PO tidak bisa dikonfirmasi
- Batch done tidak bisa dibatalkan
- Hanya batch draft yang bisa dihapus

## Security

### Access Rights
- **Purchase User**: Read, Write, Create (tidak bisa Delete)
- **Purchase Manager**: Full access (Read, Write, Create, Delete)

### Record Rules
- Multi-company support
- User hanya bisa akses batch dari company mereka

## Technical Details

### Models
- `purchase.order.batch`: Model utama untuk batch
- `purchase.order`: Extended dengan field batch_id
- `purchase.batch.wizard`: Wizard untuk create batch
- `purchase.batch.add.wizard`: Wizard untuk add PO to batch

### Key Fields
- `name`: Batch reference (auto-generated)
- `state`: Status batch
- `purchase_order_ids`: PO dalam batch
- `total_amount`: Total amount semua PO
- `partner_ids`: Vendor dari PO dalam batch

### Sequence
- Prefix: POB
- Format: POB00001, POB00002, dst.

## Installation

1. Copy module ke addons directory
2. Update apps list
3. Install "Purchase Order Batch" module
4. Module akan menambahkan menu di Purchase

## Dependencies

- `base`: Odoo base module
- `purchase`: Purchase management
- `stock`: Stock management
- `mail`: Mail and activity tracking

## Compatibility

- Odoo 16.0+
- Compatible dengan modul purchase standard
- Tidak mengubah behavior existing PO

## Support

Untuk pertanyaan atau issue, silakan hubungi developer atau buat issue di repository.