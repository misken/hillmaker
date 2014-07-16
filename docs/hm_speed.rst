The need for speed
==================

Incrementing bydatetime dataframe
---------------------------------

The standard approach is slow and non-Pythonic. It doesn't take advantage
of pandas indexing and bulk processing capabilities. The following 
StackOverflow post has several good ideas worth exploring.

[http://stackoverflow.com/questions/17552997/how-to-update-a-subset-of-a-multiindexed-pandas-dataframe](http://stackoverflow.com/questions/17552997/how-to-update-a-subset-of-a-multiindexed-pandas-dataframe)

Possibly even more relevant is:

[http://stackoverflow.com/questions/22376155/pandas-dataframe-increase-values-of-a-subset-of-a-timeframe-on-a-multi-index-d](http://stackoverflow.com/questions/22376155/pandas-dataframe-increase-values-of-a-subset-of-a-timeframe-on-a-multi-index-d)

[http://stackoverflow.com/questions/17557650/edit-pandas-dataframe-using-indexes](http://stackoverflow.com/questions/17557650/edit-pandas-dataframe-using-indexes)

[http://stackoverflow.com/questions/20754746/using-boolean-indexing-for-row-and-column-multiindex-in-pandas](http://stackoverflow.com/questions/20754746/using-boolean-indexing-for-row-and-column-multiindex-in-pandas)

[http://stackoverflow.com/questions/23419253/change-particular-column-values-in-a-pandas-multiindex-dataframe?rq=1](http://stackoverflow.com/questions/23419253/change-particular-column-values-in-a-pandas-multiindex-dataframe?rq=1)

[http://codereview.stackexchange.com/questions/43517/more-efficient-way-to-work-with-pandas-dataframes-for-stock-backtesting-exercise](http://codereview.stackexchange.com/questions/43517/more-efficient-way-to-work-with-pandas-dataframes-for-stock-backtesting-exercise)


pandas 0.14.0 introduces [MultiIndex slicers](http://pandas.pydata.org/pandas-docs/stable/whatsnew.html#whatsnew-0140-slicers)
- indexes must be fully lexsorted
- I think this is the ticket -- see alignable example at bottom of doc section

Separate dataframes by category? Dict or list of df's?
