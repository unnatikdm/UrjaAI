import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

/* -- Company branding -- */
const COMPANY = {
    name: 'Urja AI',
    tagline: 'Campus Energy Optimization System',
    addressLine1: 'Tech Park, Block C, Sector 62',
    addressLine2: 'Noida, Uttar Pradesh 201309, India',
    phone: '+91 120 456 7890',
    email: 'billing@urja-ai.com',
    website: 'www.urja-ai.com',
    gstin: '09AAACR5055K1ZG',
    cin: 'U72200UP2025PTC123456',
}

const GREEN = [22, 163, 74]
const DARK_GREEN = [20, 83, 45]
const LIGHT_BG = [236, 253, 245]
const AMBER = [217, 119, 6]
const GRAY = [100, 116, 139]

function fmtCur(amt) {
    return 'Rs. ' + amt.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function generateBillingPDF({ billingData, totals, selectedPeriod, dateRange, period }) {
    try {
        const doc = new jsPDF('p', 'mm', 'a4')
        const pageW = doc.internal.pageSize.getWidth()
        const pageH = doc.internal.pageSize.getHeight()
        const margin = 15
        let y = margin

        /* ======= HEADER BAR ======= */
        doc.setFillColor(...DARK_GREEN)
        doc.rect(0, 0, pageW, 38, 'F')

        // Accent stripe
        doc.setFillColor(...GREEN)
        doc.rect(0, 38, pageW, 2, 'F')

        // Company name
        doc.setTextColor(255, 255, 255)
        doc.setFontSize(22)
        doc.setFont('helvetica', 'bold')
        doc.text(COMPANY.name, margin, 18)

        doc.setFontSize(9)
        doc.setFont('helvetica', 'normal')
        doc.text(COMPANY.tagline, margin, 26)

        // Invoice label on right
        doc.setFontSize(16)
        doc.setFont('helvetica', 'bold')
        doc.text('ENERGY BILL', pageW - margin, 18, { align: 'right' })

        doc.setFontSize(8)
        doc.setFont('helvetica', 'normal')
        const invoiceNo = 'INV-' + new Date().getFullYear() + '-' + String(new Date().getMonth() + 1).padStart(2, '0') + '-' + String(Math.floor(Math.random() * 9000) + 1000)
        doc.text('Invoice #: ' + invoiceNo, pageW - margin, 26, { align: 'right' })
        doc.text('Generated: ' + new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }), pageW - margin, 32, { align: 'right' })

        y = 48

        /* ======= COMPANY INFO + BILLING PERIOD ======= */
        doc.setFillColor(...LIGHT_BG)
        doc.roundedRect(margin, y, pageW - margin * 2, 32, 3, 3, 'F')

        // Left: Company details
        doc.setTextColor(...DARK_GREEN)
        doc.setFontSize(8)
        doc.setFont('helvetica', 'bold')
        doc.text('FROM', margin + 5, y + 6)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(...GRAY)
        doc.text(COMPANY.addressLine1, margin + 5, y + 12)
        doc.text(COMPANY.addressLine2, margin + 5, y + 17)
        doc.text('GSTIN: ' + COMPANY.gstin, margin + 5, y + 22)
        doc.text(COMPANY.email + ' | ' + COMPANY.phone, margin + 5, y + 27)

        // Right: Billing period
        doc.setTextColor(...DARK_GREEN)
        doc.setFont('helvetica', 'bold')
        doc.text('BILLING PERIOD', pageW - margin - 5, y + 6, { align: 'right' })
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(...GRAY)
        doc.text(selectedPeriod.label + ' Statement', pageW - margin - 5, y + 12, { align: 'right' })
        doc.text(dateRange, pageW - margin - 5, y + 17, { align: 'right' })
        doc.text(selectedPeriod.days + ' days', pageW - margin - 5, y + 22, { align: 'right' })

        y += 38

        /* ======= SUMMARY BOXES ======= */
        const boxW = (pageW - margin * 2 - 9) / 4
        const boxes = [
            { label: 'TOTAL CONSUMPTION', value: totals.totalKwh.toFixed(0) + ' kWh', color: DARK_GREEN },
            { label: 'ENERGY CHARGES', value: fmtCur(totals.energyCost), color: GREEN },
            { label: 'TAXES & DUTIES', value: fmtCur(totals.gst + totals.cess), color: AMBER },
            { label: 'GRAND TOTAL', value: fmtCur(totals.grandTotal), color: DARK_GREEN },
        ]

        boxes.forEach((box, i) => {
            const x = margin + i * (boxW + 3)
            doc.setFillColor(255, 255, 255)
            doc.setDrawColor(220, 220, 220)
            doc.roundedRect(x, y, boxW, 20, 2, 2, 'FD')

            doc.setTextColor(...GRAY)
            doc.setFontSize(6)
            doc.setFont('helvetica', 'bold')
            doc.text(box.label, x + boxW / 2, y + 7, { align: 'center' })

            doc.setTextColor(...box.color)
            doc.setFontSize(12)
            doc.setFont('helvetica', 'bold')
            doc.text(box.value, x + boxW / 2, y + 16, { align: 'center' })
        })

        y += 27

        /* ======= BUILDING-WISE TABLE ======= */
        doc.setTextColor(...DARK_GREEN)
        doc.setFontSize(11)
        doc.setFont('helvetica', 'bold')
        doc.text('Building-Wise Consumption & Charges', margin, y)
        y += 4

        const tableBody = billingData.map((b, i) => {
            const pct = totals.totalKwh > 0 ? (b.kwh / totals.totalKwh * 100).toFixed(1) : '0.0'
            return [
                i + 1,
                b.name,
                b.dailyAvg.toFixed(1) + ' kWh',
                b.kwh.toFixed(0) + ' kWh',
                fmtCur(b.cost),
                pct + '%',
            ]
        })

        autoTable(doc, {
            startY: y,
            margin: { left: margin, right: margin },
            head: [['#', 'Building', 'Daily Avg', selectedPeriod.label + ' Total', 'Energy Charges', 'Share']],
            body: tableBody,
            theme: 'grid',
            headStyles: {
                fillColor: DARK_GREEN,
                textColor: [255, 255, 255],
                fontSize: 8,
                fontStyle: 'bold',
                halign: 'center',
            },
            bodyStyles: {
                fontSize: 8,
                textColor: [51, 65, 85],
            },
            columnStyles: {
                0: { halign: 'center', cellWidth: 10 },
                1: { fontStyle: 'bold', cellWidth: 38 },
                2: { halign: 'right' },
                3: { halign: 'right' },
                4: { halign: 'right', fontStyle: 'bold' },
                5: { halign: 'center' },
            },
            alternateRowStyles: { fillColor: [248, 255, 248] },
            styles: { cellPadding: 3 },
        })

        y = doc.lastAutoTable.finalY + 8

        /* ======= TOTALS BREAKDOWN ======= */
        const totalsX = pageW - margin - 80
        const totalsW = 80

        doc.setFillColor(...LIGHT_BG)
        doc.roundedRect(totalsX, y, totalsW, 52, 2, 2, 'F')

        let ty = y + 7
        const addRow = (label, value, bold, color) => {
            doc.setTextColor(...(color || GRAY))
            doc.setFontSize(8)
            doc.setFont('helvetica', bold ? 'bold' : 'normal')
            doc.text(label, totalsX + 4, ty)
            doc.text(value, totalsX + totalsW - 4, ty, { align: 'right' })
            ty += 6
        }

        addRow('Energy Charges', fmtCur(totals.energyCost))
        addRow('Fixed / Demand Charges', fmtCur(totals.fixedCharge))

        doc.setDrawColor(180, 200, 180)
        doc.line(totalsX + 4, ty - 2, totalsX + totalsW - 4, ty - 2)
        ty += 2

        addRow('Subtotal', fmtCur(totals.subtotal))
        addRow('GST (18%)', fmtCur(totals.gst))
        addRow('Energy Cess (1%)', fmtCur(totals.cess))

        doc.setDrawColor(...GREEN)
        doc.setLineWidth(0.5)
        doc.line(totalsX + 4, ty - 1, totalsX + totalsW - 4, ty - 1)
        ty += 3

        addRow('GRAND TOTAL', fmtCur(totals.grandTotal), true, DARK_GREEN)

        y = ty + 8

        /* ======= TARIFF SCHEDULE ======= */
        if (y + 35 > pageH - 30) {
            doc.addPage()
            y = margin
        }

        doc.setTextColor(...DARK_GREEN)
        doc.setFontSize(11)
        doc.setFont('helvetica', 'bold')
        doc.text('Tariff Schedule (Commercial)', margin, y)
        y += 4

        autoTable(doc, {
            startY: y,
            margin: { left: margin, right: margin },
            head: [['Slab', 'Consumption Range', 'Rate (Rs./kWh)']],
            body: [
                ['1', '0 - 100 kWh', 'Rs. 5.50'],
                ['2', '101 - 300 kWh', 'Rs. 7.00'],
                ['3', '301 - 500 kWh', 'Rs. 8.50'],
                ['4', '500+ kWh', 'Rs. 10.00'],
            ],
            theme: 'striped',
            headStyles: { fillColor: GREEN, textColor: [255, 255, 255], fontSize: 8, fontStyle: 'bold', halign: 'center' },
            bodyStyles: { fontSize: 8, halign: 'center', textColor: [51, 65, 85] },
            styles: { cellPadding: 2.5 },
            tableWidth: 100,
        })

        y = doc.lastAutoTable.finalY + 6

        /* ======= NOTES ======= */
        doc.setTextColor(...GRAY)
        doc.setFontSize(7)
        doc.setFont('helvetica', 'italic')
        const notes = [
            '* Rates are indicative and based on standard Indian commercial electricity tariffs.',
            '* Actual charges may vary based on state/UT regulations and utility provider.',
            '* This is a computer-generated report and does not require a physical signature.',
            '* For queries, contact ' + COMPANY.email + ' or call ' + COMPANY.phone + '.',
        ]
        notes.forEach((n) => {
            if (y + 5 > pageH - 20) { doc.addPage(); y = margin }
            doc.text(n, margin, y)
            y += 4.5
        })

        /* ======= FOOTER ======= */
        const footerY = pageH - 12
        doc.setFillColor(...DARK_GREEN)
        doc.rect(0, footerY - 4, pageW, 16, 'F')
        doc.setFillColor(...GREEN)
        doc.rect(0, footerY - 6, pageW, 2, 'F')

        doc.setTextColor(255, 255, 255)
        doc.setFontSize(7)
        doc.setFont('helvetica', 'normal')
        doc.text(COMPANY.name + ' | ' + COMPANY.tagline + ' | CIN: ' + COMPANY.cin, pageW / 2, footerY + 1, { align: 'center' })
        doc.text(COMPANY.website + ' | ' + COMPANY.email, pageW / 2, footerY + 6, { align: 'center' })

        /* ======= SAVE via blob + link for max compatibility ======= */
        const filename = 'UrjaAI_EnergyBill_' + selectedPeriod.id + '_' + new Date().toISOString().slice(0, 10) + '.pdf'

        const blob = doc.output('blob')
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        setTimeout(() => URL.revokeObjectURL(url), 1000)

        console.log('[BillingPDF] Download triggered:', filename)
    } catch (err) {
        console.error('[BillingPDF] PDF generation failed:', err)
        alert('Failed to generate PDF report. Error: ' + err.message)
    }
}
