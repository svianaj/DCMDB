import kerchunk
from kerchunk.combine import MultiZarrToZarr


def export_dict_to_parq(dictionary, fname):
    """Export dict reference to parquet."""
    kerchunk.df.refs_to_dataframe(dictionary, fname)
    return


def combine_joined_reference_parquet(ref_files):
    out_dict = MultiZarrToZarr(
        ref_files,
        remote_protocol="file",
        concat_dims=["time"],
        coo_map={
            "time": "INDEX"
        },  # "data:time"}, does not work as time is missing in some/all files
        identical_dims=["lat", "lon", "y", "x", "forecast_offset", "level"],
    ).translate()

    return out_dict
