import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class PrefilterSeq:
    data = None

    def __init__(self, data, list_filter):
        self.list_filter = list_filter
        self.data = data
        self._prepare()

    def _prepare(self):
        # расчет чека
        self.data['price'] = self.data['sales_value'] / (np.maximum(self.data['quantity'], 1))

    def processing(self):
        # последовательное применение фильтров
        # использование:
        # process_list=[FilterLower(low=1), FilterMax(max=60), FilterNonDepartment(item_features),
        #               OverPopular(popularity=0.5), LowestPopularity(popularity=0.01), LongTimeNoSold(weeks=62),
        #               TopBayer(take_n_popular=5000)]
        for filter in self.list_filter:
            self.data = filter.trans(self.data)

        return self.data


class Filter(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def trans(self, data):
        pass

# фильтр <
class FilterLower(Filter):
    def __init__(self, low=1):
        super().__init__()
        self.low = low

    def trans(self, data):
        return data[data['price'] > self.low]


# фильтр >
class FilterMax(Filter):
    def __init__(self, max=60):
        super().__init__()
        self.max = max

    def trans(self, data):
        return data[data['price'] < self.max]


# сложный фильтр по разделам
class FilterNonDepartment(Filter):
    def __init__(self, item_features):
        super().__init__()
        self.item_features = item_features

    def trans(self, data):
        if self.item_features is not None:
            department_size = pd.DataFrame(self.item_features. \
                                           groupby('department')['item_id'].nunique(). \
                                           sort_values(ascending=False)).reset_index()

            department_size.columns = ['department', 'n_items']
            rare_departments = department_size[department_size['n_items'] < 150].department.tolist()
            items_in_rare_departments = self.item_features[
                self.item_features['department'].isin(rare_departments)].item_id.unique().tolist()

            data = data[~data['item_id'].isin(items_in_rare_departments)]
            return data


class Popular(Filter):
    df_popularity = None

    def __init__(self):
        super().__init__()

    @abstractmethod
    def trans(self, data):
        self.df_popularity = data.groupby('item_id')['user_id'].nunique().reset_index()
        self.df_popularity['share_unique_users'] = self.df_popularity['user_id'] / data['user_id'].nunique()


# слишком сильно популярные
class OverPopular(Popular):
    def __init__(self, popularity=0.5):
        super().__init__()
        self.popularity = popularity

    def trans(self, data):
        super().trans(data)

        top_popular = self.df_popularity[self.df_popularity['share_unique_users'] > self.popularity].item_id.tolist()
        data = data[~data['item_id'].isin(top_popular)]
        return data


# слабо популярные
class LowestPopularity(Popular):
    def __init__(self, popularity=0.01):
        super().__init__()
        self.popularity = popularity

    def trans(self, data):
        super().trans(data)

        top_notpopular = self.df_popularity[self.df_popularity['share_unique_users'] < self.popularity].item_id.tolist()
        data = data[~data['item_id'].isin(top_notpopular)]
        return data


# давно не продаваемые
class LongTimeNoSold(Filter):
    def __init__(self, weeks=52):
        super().__init__()
        self.weeks = weeks

    def trans(self, data):
        # уберем товары, которые не продавались за последние 12 мес¤цев
        week_of_last_purchaices = data.groupby('item_id')['week_no'].max().reset_index()
        bought_year_ago = week_of_last_purchaices[
            week_of_last_purchaices['week_no'] < (data['week_no'].max() - self.weeks)].item_id.tolist()
        data = data[~data['item_id'].isin(bought_year_ago)]
        return data


# покупатель товаров в топ (5000)
class TopBayer(Filter):
    def __init__(self, take_n_popular=5000):
        super().__init__()
        self.take_n_popular = take_n_popular

    def trans(self, data):
        popularity = data.groupby('item_id')['quantity'].sum().reset_index()
        popularity.rename(columns={'quantity': 'n_sold'}, inplace=True)
        top = popularity.sort_values('n_sold', ascending=False).head(self.take_n_popular).item_id.tolist()
        data.loc[~data['item_id'].isin(top), 'item_id'] = 999999
        return data


def postfilter_items(user_id, recommednations):
    pass
