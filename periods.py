from scipy.stats import kstest
import numpy as np

# class for storing count means of spectrums for different time periods
class PdfPeriod:
    def __init__(self, seccode: str):
        seccode = seccode
        self.bids = np.zeros((3, 10))
        self.asks = np.zeros((3, 10))

    def calc_avgs(self, df_spectrum):
        """
        calculates averages by count for 3 time periods
        pd: DataFrame with the following columns ['NO', 'SECCODE', 'TIMESTAMP', 'BID_ASK']
        """
        total_count = [0, 0, 0]
        per = -1

        for _, _, timestamp, spectrum_str in df_spectrum.values:
            spectrum = [float(el) for el in spectrum_str[1:-1].split(',')]
            time_cur = timestamp//100000000

            # define time period
            if   time_cur < 1500: per = 0
            elif time_cur < 1900: per = 1
            else:                 per = 2

            for i in range(10): 
                self.bids[per][i] += spectrum[i]
                self.asks[per][i] += spectrum[10 + i]
            total_count[per] += 1
        
        # calculate averages
        for i in range(3):
            self.bids[i] = self.bids[i]/total_count[i]
            self.asks[i] = self.asks[i]/total_count[i]

    @staticmethod
    def _calc_cdf(lst):
        """
        calculates CDF

        lst: a list of numbers (pdf)
        """

        s = 0
        cdf = [0] * len(lst)
        for index, numb in enumerate(lst):
            cdf[index] = s + numb
            s += numb

        return cdf

    @staticmethod
    def kstest(pdf1: list, pdf2: list, alpha) -> float:
        """
        method for performing ks-test by given pdfs

        returns pval
        """

        pval = kstest(PdfPeriod._calc_cdf(pdf1),
                      PdfPeriod._calc_cdf(pdf2)).pvalue
        if pval < (1-alpha):
            return False
        else:
            return True

    def compare_by_periods(self, date: str):
        """
        compare bids and asks in different periods of time
        """
        result = [date]
        for i, j in [(0, 1),(1, 2),(0, 2)]:
            comp_bids = PdfPeriod.kstest(self.bids[i], self.bids[j], 0.975)
            comp_asks = PdfPeriod.kstest(self.asks[i], self.asks[j], 0.975)
            answer = str(comp_bids)+', '+str(comp_asks)
            result.append(answer)
        return result
    
    def compare_by_days(self, entry, date: str):
        """
        compare bids and asks with the previous day
        """
        result = [date]
        for i in range(3):
            comp_bids = PdfPeriod.kstest(self.bids[i], entry[0][i], 0.975)
            comp_asks = PdfPeriod.kstest(self.asks[i], entry[1][i], 0.975)
            answer = str(comp_bids)+', '+str(comp_asks)
            result.append(answer)
        return result