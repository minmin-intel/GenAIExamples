link1="https://www.intc.com/news-events/press-releases/detail/1692/intel-reports-first-quarter-2024-financial-results"
link2="https://www.intc.com/news-events/press-releases/detail/1672/intel-reports-fourth-quarter-and-full-year-2023-financial"
http_proxy="" curl -X POST "http://${host_ip}:6007/v1/dataprep" \
     -H "Content-Type: multipart/form-data" \
     -F "link_list=[${link1},${link2}]" \