import { buildReportDoc, reportFileName } from "./reportPdfDoc";

// Creates the designed PDF for a report and downloads it. pdfmake (~2 MB with its fonts) is loaded
// only when a teacher clicks Download, so it doesn't slow down the dashboard.
export async function downloadReportPdf(report) {
  const [{ default: pdfMake }, { default: vfs }] = await Promise.all([import("pdfmake/build/pdfmake"), import("pdfmake/build/vfs_fonts")]);
  pdfMake.vfs = vfs; // pdfmake 0.2.x: vfs_fonts exports the Roboto font files
  await new Promise((resolve, reject) => {
    try {
      pdfMake.createPdf(buildReportDoc(report)).download(reportFileName(report), resolve);
    } catch (error) {
      reject(error);
    }
  });
}
