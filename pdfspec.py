from scipy.stats import kstest


# class for storing time and count means of spectrums
class PdfSpec:
    def __init__(self, seccode: str):
        seccode = seccode
        self.bids_count = [0] * 10
        self.bids_time = [0] * 10
        self.asks_count = [0] * 10
        self.asks_time = [0] * 10
        self.n = 0

    def calc_avgs(self, df_spectrum):
        """
        calculates averages by count and by time
        pd: DataFrame with the following columns ['NO', 'SECCODE', 'TIMESTAMP', 'BID_ASK']
        """
        prev_time = df_spectrum.iloc[0]['TIMESTAMP']
        total_count = len(df_spectrum)
        total_time = 0

        for _, _, timestamp, spectrum_str in df_spectrum.values:
            spectrum = [float(el) for el in spectrum_str[1:-1].split(',')]
            # calculating avg by count
            for i in range(10):
                self.bids_count[i] += spectrum[i]
                self.asks_count[i] += spectrum[10 + i]

            # calculating avg by time
            w = timestamp - prev_time
            for i in range(10):
                self.bids_time[i] += (spectrum[i] * w)
                self.asks_time[i] += (spectrum[10 + i] * w)
            total_time += w

            prev_time = timestamp

        self.bids_count = [bid / total_count for bid in self.bids_count]
        self.asks_count = [ask / total_count for ask in self.asks_count]

        self.bids_time = [bid / total_time for bid in self.bids_time]
        self.asks_time = [ask / total_time for ask in self.asks_time]

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
    def kstest(pdf1: list, pdf2: list) -> float:
        """
        method for performing ks-test by given pdfs

        returns pval
        """

        return kstest(PdfSpec._calc_cdf(pdf1),
                      PdfSpec._calc_cdf(pdf2)).pvalue

