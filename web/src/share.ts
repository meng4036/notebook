import { toBlob } from 'html-to-image'
import { PDFDocument } from 'pdf-lib'

export async function cardToPng(el: HTMLElement): Promise<Blob> {
  const blob = await toBlob(el, {
    pixelRatio: 2,
    backgroundColor: '#ffffff',
    cacheBust: true,
  })
  if (!blob) throw new Error('png failed')
  return blob
}

function downloadBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export async function sharePng(blob: Blob, name: string): Promise<'shared' | 'downloaded'> {
  const file = new File([blob], name, { type: 'image/png' })
  const nav = navigator as Navigator & {
    canShare?: (d: ShareData) => boolean
  }
  try {
    if (nav.canShare?.({ files: [file] })) {
      await navigator.share({ files: [file], title: '练习卡' })
      return 'shared'
    }
  } catch (e) {
    if ((e as DOMException).name === 'AbortError') return 'shared'
  }
  downloadBlob(blob, name)
  return 'downloaded'
}

export async function savePdf(png: Blob, name: string) {
  const bytes = new Uint8Array(await png.arrayBuffer())
  const pdf = await PDFDocument.create()
  const img = await pdf.embedPng(bytes)
  const page = pdf.addPage([img.width, img.height])
  page.drawImage(img, { x: 0, y: 0, width: img.width, height: img.height })
  const out = await pdf.save()
  const buf = new ArrayBuffer(out.byteLength)
  new Uint8Array(buf).set(out)
  downloadBlob(new Blob([buf], { type: 'application/pdf' }), name)
}
